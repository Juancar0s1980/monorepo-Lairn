"""
Evaluación de la regla de alerta temprana (HU-10.2).

Actividades de un estudiante dentro de un programa:
  - Evaluación formal presentada (cuestionario): % = aciertos / preguntas.
  - Tarea calificada: % = nota / 5 × 100.
Actividades de un curso (asignatura): por cada actividad, el promedio del
grupo (en evaluaciones formales, solo las preguntas de esa asignatura).

Una alerta se dispara con `actividades_minimas` o más actividades por debajo
de `porcentaje_minimo`. No se duplican: la alerta abierta se actualiza; si la
condición desaparece, pasa a `resuelta`; si el Coordinador ya la atendió, solo
se abre otra cuando la situación empeora (más actividades bajas).
"""

from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    EntregaTarea,
    EvaluacionPregunta,
    IntentoEvaluacion,
    OpcionesIntegridad,
    OpcionesEstadoAlerta,
    OpcionesTipoAlerta,
    OpcionesTipoEvaluacion,
    ProgramaAcademico,
    ReglaAlerta,
)
from .servicio_presentacion import GRACIA_SEGUNDOS, cerrar_si_vencido


def _actividades(programa):
    """Retorna (por_estudiante, por_curso).

    por_estudiante[est_id] = [ {tipo, nombre, asignatura, porcentaje} ]
    por_curso[asignatura_id] = [ {tipo, nombre, asignatura, porcentaje, estudiantes} ]
    """
    for intento in IntentoEvaluacion.objects.filter(
        enviado_en__isnull=True, evaluacion__momento__programa=programa,
        vence_en__lt=timezone.now() - timedelta(seconds=GRACIA_SEGUNDOS),
    ):
        cerrar_si_vencido(intento)

    por_estudiante = defaultdict(list)
    curso_acumulado = defaultdict(lambda: {'suma': 0.0, 'n': 0})  # (asig_id, clave_actividad)
    info_curso = {}

    # Los anulados por fraude (ADR-010) no son una medida de desempeño.
    intentos = list(IntentoEvaluacion.objects.filter(
        enviado_en__isnull=False, evaluacion__momento__programa=programa,
        evaluacion__tipo=OpcionesTipoEvaluacion.CUESTIONARIO,
    ).exclude(integridad=OpcionesIntegridad.ANULADO_FRAUDE).select_related('evaluacion'))
    preguntas = defaultdict(list)
    for item in EvaluacionPregunta.objects.filter(
        evaluacion_id__in={i.evaluacion_id for i in intentos},
    ).select_related('pregunta__asignatura'):
        preguntas[item.evaluacion_id].append(item.pregunta)

    for intento in intentos:
        lista = preguntas[intento.evaluacion_id]
        if not lista:
            continue
        aciertos_por_asig = defaultdict(lambda: [0, 0])
        for p in lista:
            aciertos_por_asig[p.asignatura_id][1] += 1
            if intento.respuestas.get(str(p.id)) == p.respuesta_correcta:
                aciertos_por_asig[p.asignatura_id][0] += 1
        total_a = sum(a for a, _ in aciertos_por_asig.values())
        codigos = sorted({p.asignatura.codigo for p in lista})
        por_estudiante[intento.estudiante_id].append({
            'tipo': 'evaluacion', 'nombre': intento.evaluacion.nombre, 'asignatura': ', '.join(codigos),
            'porcentaje': round(100 * total_a / len(lista), 1),
        })
        for asig_id, (a, n) in aciertos_por_asig.items():
            clave = (asig_id, f'e{intento.evaluacion_id}')
            curso_acumulado[clave]['suma'] += 100 * a / n
            curso_acumulado[clave]['n'] += 1
            info_curso[clave] = {'tipo': 'evaluacion', 'nombre': intento.evaluacion.nombre}

    for entrega in EntregaTarea.objects.filter(
        nota__isnull=False, tarea__asignatura__programa=programa,
    ).select_related('tarea__asignatura'):
        porcentaje = round(float(entrega.nota) / 5 * 100, 1)
        asignatura = entrega.tarea.asignatura
        por_estudiante[entrega.estudiante_id].append({
            'tipo': 'tarea', 'nombre': entrega.tarea.titulo, 'asignatura': asignatura.codigo, 'porcentaje': porcentaje,
        })
        clave = (asignatura.id, f't{entrega.tarea_id}')
        curso_acumulado[clave]['suma'] += porcentaje
        curso_acumulado[clave]['n'] += 1
        info_curso[clave] = {'tipo': 'tarea', 'nombre': entrega.tarea.titulo}

    por_curso = defaultdict(list)
    for (asig_id, clave), acum in curso_acumulado.items():
        por_curso[asig_id].append({
            **info_curso[(asig_id, clave)], 'porcentaje': round(acum['suma'] / acum['n'], 1),
            'estudiantes': acum['n'],
        })
    return por_estudiante, por_curso


def _aplicar(programa, tipo, clave_campo, clave_valor, actividades, regla, vistos):
    bajas = [a for a in actividades if a['porcentaje'] < regla.porcentaje_minimo]
    filtro = {'programa': programa, 'tipo': tipo, clave_campo: clave_valor}
    ultima = AlertaDesempeno.objects.filter(**filtro).order_by('-creada_en').first()
    if len(bajas) < regla.actividades_minimas:
        return None
    vistos.add((tipo, clave_valor))
    datos = {'actividades_bajas': len(bajas), 'total_actividades': len(actividades), 'detalle': bajas}
    if ultima and ultima.estado == OpcionesEstadoAlerta.ABIERTA:
        for campo, valor in datos.items():
            setattr(ultima, campo, valor)
        ultima.save()
        return 'actualizada'
    if ultima and ultima.estado == OpcionesEstadoAlerta.ATENDIDA and len(bajas) <= ultima.actividades_bajas:
        return None  # ya atendida y no empeoró
    AlertaDesempeno.objects.create(**filtro, **datos)
    return 'creada'


def evaluar_alertas(programa=None) -> dict:
    regla = ReglaAlerta.vigente()
    resumen = {'creadas': 0, 'actualizadas': 0, 'resueltas': 0}
    if not regla.activa:
        return resumen
    programas = [programa] if programa else ProgramaAcademico.objects.filter(activo=True)
    for prog in programas:
        por_estudiante, por_curso = _actividades(prog)
        vistos = set()
        for est_id, actividades in por_estudiante.items():
            r = _aplicar(prog, OpcionesTipoAlerta.ESTUDIANTE, 'estudiante_id', est_id, actividades, regla, vistos)
            if r:
                resumen[f'{r}s'] += 1
        for asig_id, actividades in por_curso.items():
            r = _aplicar(prog, OpcionesTipoAlerta.CURSO, 'asignatura_id', asig_id, actividades, regla, vistos)
            if r:
                resumen[f'{r}s'] += 1
        # Las abiertas que ya no cumplen la condición se resuelven solas.
        for alerta in AlertaDesempeno.objects.filter(programa=prog, estado=OpcionesEstadoAlerta.ABIERTA):
            clave = alerta.estudiante_id if alerta.tipo == OpcionesTipoAlerta.ESTUDIANTE else alerta.asignatura_id
            if (alerta.tipo, clave) not in vistos:
                alerta.estado = OpcionesEstadoAlerta.RESUELTA
                alerta.save(update_fields=['estado', 'actualizada_en'])
                resumen['resueltas'] += 1
    return resumen
