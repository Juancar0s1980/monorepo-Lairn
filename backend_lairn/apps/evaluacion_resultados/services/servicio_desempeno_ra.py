"""
Porcentaje de acierto por resultado de aprendizaje (HU-09.1).

MÉTRICA PROVISIONAL: el backlog pide definir las métricas con Vicerrectoría
antes de esta épica. Mientras tanto se usa una definición explícita y fácil
de cambiar en un solo lugar:

- Fuente: intentos ENVIADOS de evaluaciones formales tipo cuestionario.
- Los intentos ANULADOS POR FRAUDE (ADR-010) se excluyen del % de acierto y
  se informan aparte en `resumen.anulados_fraude`.
- Por cada pregunta presentada: acierto si la opción guardada es la
  correcta; sin responder cuenta como no acertada.
- % individual (estudiante, RA) = aciertos / preguntas presentadas del RA.
- % grupal (RA) = Σ aciertos / Σ preguntas presentadas de todos los estudiantes.
- Las tareas (nota de rúbrica) no entran en el % de acierto.
"""

from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.evaluacion_resultados.models import (
    EvaluacionPregunta,
    IntentoEvaluacion,
    OpcionesIntegridad,
    OpcionesTipoEvaluacion,
)
from .servicio_presentacion import GRACIA_SEGUNDOS, cerrar_si_vencido
from .escala_institucional import NIVELES as ESCALA_NIVELES, NIVELES_APROBADOS, nivel as nivel_institucional

# ============================================================================
# MÉTRICA PROVISIONAL (ADR-006 / ADR-011). Único lugar para ajustarla cuando
# Vicerrectoría la defina (HU-09.2/09.3). Toda pantalla y exportación que la
# use muestra el aviso "métrica provisional".
# ============================================================================
METRICA_PROVISIONAL = {
    # ¿Una pregunta sin responder cuenta como no acertada (True) o se excluye (False)?
    'sin_responder_es_fallo': True,
    # % de acierto desde el cual un RA se considera logrado.
    'umbral_logro_porcentaje': 60,
    # Niveles de desempeño (ADR-019): escala institucional, ver `escala_institucional`.
    'niveles': [(c, e, float(m)) for c, e, m in ESCALA_NIVELES],
    # Niveles que cuentan como aprobación (nota >= 3,0, Acuerdo 005 Art. 46).
    'niveles_aprobados': list(NIVELES_APROBADOS),
}


def evaluar_respuesta(respuestas: dict, pregunta):
    """True/False si cuenta como acierto/fallo; None si la pregunta se excluye del cálculo."""
    marcada = respuestas.get(str(pregunta.id))
    if marcada is None:
        return False if METRICA_PROVISIONAL['sin_responder_es_fallo'] else None
    return marcada == pregunta.respuesta_correcta


def nivel_de_nota(nota: float) -> str:
    """Nivel con la escala institucional, tras el redondeo reglamentario a un decimal (ADR-019)."""
    return nivel_institucional(nota)


def ra_logrado(porcentaje) -> bool | None:
    if porcentaje is None:
        return None
    return porcentaje >= METRICA_PROVISIONAL['umbral_logro_porcentaje']


def _porcentaje(aciertos: int, presentadas: int):
    return round(100 * aciertos / presentadas, 1) if presentadas else None


porcentaje = _porcentaje


def desempeno_por_ra(programa, momento_id=None, evaluacion_id=None) -> dict:
    # Intentos vencidos que nadie ha vuelto a abrir: se cierran (envío automático
    # HU-07.3) antes de contar, para no dejarlos fuera del tablero.
    vencidos = IntentoEvaluacion.objects.filter(
        enviado_en__isnull=True, evaluacion__momento__programa=programa,
        vence_en__lt=timezone.now() - timedelta(seconds=GRACIA_SEGUNDOS),
    )
    for intento in vencidos:
        cerrar_si_vencido(intento)
    intentos = IntentoEvaluacion.objects.filter(
        enviado_en__isnull=False,
        evaluacion__momento__programa=programa,
        evaluacion__tipo=OpcionesTipoEvaluacion.CUESTIONARIO,
    ).select_related('estudiante')
    if momento_id:
        intentos = intentos.filter(evaluacion__momento_id=momento_id)
    if evaluacion_id:
        intentos = intentos.filter(evaluacion_id=evaluacion_id)
    anulados_fraude = intentos.filter(integridad=OpcionesIntegridad.ANULADO_FRAUDE).count()
    intentos = intentos.exclude(integridad=OpcionesIntegridad.ANULADO_FRAUDE)
    intentos = list(intentos)

    # Preguntas de cada evaluación (congeladas al publicar) con su RA.
    items = EvaluacionPregunta.objects.filter(
        evaluacion_id__in={i.evaluacion_id for i in intentos},
    ).select_related('pregunta__resultado__competencia', 'pregunta__asignatura')
    preguntas_por_eval = defaultdict(list)
    info_ra = {}
    for item in items:
        p = item.pregunta
        preguntas_por_eval[item.evaluacion_id].append(p)
        info_ra[p.resultado_id] = {
            'resultado_id': p.resultado_id, 'descripcion': p.resultado.descripcion,
            'competencia': p.resultado.competencia.nombre, 'asignatura': p.asignatura.codigo,
        }

    grupal = defaultdict(lambda: {'aciertos': 0, 'presentadas': 0, 'estudiantes': set()})
    individual = defaultdict(lambda: defaultdict(lambda: {'aciertos': 0, 'presentadas': 0}))
    estudiantes = {}
    for intento in intentos:
        estudiantes[intento.estudiante_id] = intento.estudiante
        for p in preguntas_por_eval[intento.evaluacion_id]:
            acierto = evaluar_respuesta(intento.respuestas, p)
            if acierto is None:
                continue
            for acumulado in (grupal[p.resultado_id], individual[intento.estudiante_id][p.resultado_id]):
                acumulado['presentadas'] += 1
                acumulado['aciertos'] += int(acierto)
            grupal[p.resultado_id]['estudiantes'].add(intento.estudiante_id)

    filas_grupal = sorted(
        (
            {**info_ra[ra], 'aciertos': g['aciertos'], 'presentadas': g['presentadas'],
             'estudiantes': len(g['estudiantes']), 'porcentaje': _porcentaje(g['aciertos'], g['presentadas'])}
            for ra, g in grupal.items()
        ),
        key=lambda f: (f['porcentaje'] if f['porcentaje'] is not None else 101),
    )
    filas_individual = []
    for est_id, por_ra in individual.items():
        est = estudiantes[est_id]
        total_a = sum(v['aciertos'] for v in por_ra.values())
        total_p = sum(v['presentadas'] for v in por_ra.values())
        filas_individual.append({
            'estudiante': {'id': est.id, 'email': est.email,
                           'nombre': f'{est.first_name} {est.first_last_name}'.strip()},
            'por_ra': {str(ra): {**v, 'porcentaje': _porcentaje(v['aciertos'], v['presentadas'])}
                       for ra, v in por_ra.items()},
            'porcentaje_total': _porcentaje(total_a, total_p),
        })
    filas_individual.sort(key=lambda f: f['estudiante']['nombre'].lower())

    return {
        'resumen': {
            'evaluaciones': len({i.evaluacion_id for i in intentos}),
            'intentos': len(intentos), 'estudiantes': len(estudiantes),
            'anulados_fraude': anulados_fraude,
        },
        'grupal': filas_grupal,
        'individual': filas_individual,
    }
