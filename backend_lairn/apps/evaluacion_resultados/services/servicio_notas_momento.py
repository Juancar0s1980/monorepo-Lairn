"""
Notas del momento por estudiante (ADR-019).

Reglas (ver LAIRN/11-Analisis-notas-momento-tercer-corte.md):
  - Examen: todos los cuestionarios publicados del momento son partes de un mismo examen y se
    consolidan por cantidad de preguntas: nota = 5 x correctas / total. Correctas, incorrectas
    (respondidas) y sin responder salen de las respuestas reales guardadas en cada intento.
  - Trabajo: evaluaciones tipo tarea del momento (opcional). Varias => promedio simple.
  - Consolidado del momento: si no hay trabajo, = examen. Con trabajo, ponderación del esquema
    (peso_examen / peso_trabajo); si no está definida, queda pendiente (nunca se inventa).
  - Redondeo reglamentario a un decimal UNA sola vez, sobre el valor crudo (Acuerdo 005, Art. 45).
  - Un dato ausente nunca se vuelve 0 en la calificación registrada. Aparte, la "nota
    reglamentaria a reportar" aplica 0,0 SOLO a lo no presentado sin excusa (Acuerdo 005).
  - Aportes: al tercer corte = consolidado x peso del momento; a la definitiva = además x peso
    del tercer corte. Son aportes, no la nota del corte (las demás actividades no están aquí).
  - No modifica IntentoEvaluacion.nota ni EntregaTarea.nota.
"""

from collections import defaultdict
from decimal import Decimal

from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AsistenciaEvaluacion,
    EntregaTarea,
    EsquemaCalificacion,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    OpcionesEstadoEvaluacion,
    OpcionesIntegridad,
    OpcionesTipoEvaluacion,
)
from .escala_institucional import (
    ETIQUETA_NIVEL,
    FUENTES,
    NIVELES,
    NOTA_APROBACION,
    PESO_MOMENTO_EN_TERCER_CORTE,
    PESO_TERCER_CORTE_EN_DEFINITIVA,
    aprueba,
    nivel,
    redondear,
)
from .servicio_presentacion import cerrar_si_vencido, origenes_convocatoria
from .servicio_supervision import nombre_completo
from .servicio_tareas import estado_plazo

META_APROBACION_PCT = Decimal('70')   # Res. 0238/2024 según la propuesta (indicador RF-29)
META_PROMEDIO = Decimal('3.0')

# Estados de una parte del examen (de mayor a menor prioridad para el estado general).
ESTADOS_EXAMEN = {
    'anulado': 'Anulado por fraude',
    'suspendido': 'Suspendido (integridad)',
    'en_curso': 'En curso',
    'pendiente': 'Pendiente: la evaluación sigue abierta',
    'excusa': 'Con excusa · supletorio pendiente',
    'ausente': 'Ausente',
    'no_presento': 'No presentó',
    'presento': 'Presentó',
    'incompleto': 'Presentó parcialmente',
    'no_aplica': 'No aplica',
}
PRIORIDAD_EXAMEN = ['anulado', 'suspendido', 'en_curso', 'pendiente', 'excusa', 'ausente', 'no_presento']
ESTADOS_TRABAJO = {
    'calificado': 'Calificado',
    'pendiente_calificar': 'Entregado · pendiente de calificar',
    'pendiente_entrega': 'Pendiente: el plazo sigue abierto',
    'no_entrego': 'No entregó',
    'incompleto': 'Entregó parcialmente',
    'no_aplica': 'No aplica (sin trabajo en el momento)',
}
PRIORIDAD_TRABAJO = ['pendiente_calificar', 'pendiente_entrega', 'no_entrego']
ESTADOS_CONSOLIDADO = {
    'calificado': 'Calificado',
    'pendiente': 'Pendiente',
    'ponderacion_sin_definir': 'Pendiente: ponderación examen/trabajo sin definir',
}
# Estados que el reglamento califica con 0,0 cuando no hay excusa (Acuerdo 005).
SIN_EXCUSA_EXAMEN = {'ausente', 'no_presento'}


def _dec(valor):
    return None if valor is None else Decimal(str(valor))


def _f(valor, decimales=1):
    """Decimal → float para JSON/Excel (None se conserva)."""
    if valor is None:
        return None
    return float(Decimal(valor).quantize(Decimal(1).scaleb(-decimales)))


# ------------------------------------------------------------------ esquema

def esquema_efectivo(momento) -> dict:
    """Pesos vigentes del momento con su origen: 'momento' | 'institucional' | 'reglamento' | None."""
    propio = EsquemaCalificacion.objects.filter(momento=momento).first()
    inst = EsquemaCalificacion.objects.filter(momento__isnull=True).first()
    constantes = {'peso_momento_en_corte': PESO_MOMENTO_EN_TERCER_CORTE,
                  'peso_corte_en_definitiva': PESO_TERCER_CORTE_EN_DEFINITIVA}
    salida = {}
    for campo in ('peso_momento_en_corte', 'peso_corte_en_definitiva', 'peso_examen', 'peso_trabajo'):
        if propio is not None and getattr(propio, campo) is not None:
            salida[campo], origen = getattr(propio, campo), 'momento'
        elif inst is not None and getattr(inst, campo) is not None:
            salida[campo], origen = getattr(inst, campo), 'institucional'
        elif campo in constantes:
            salida[campo], origen = constantes[campo], 'reglamento'
        else:
            salida[campo], origen = None, None
        salida[f'origen_{campo}'] = origen
    salida['ponderacion_definida'] = salida['peso_examen'] is not None and salida['peso_trabajo'] is not None
    return salida


# ------------------------------------------------------------------ partes del examen

def _estado_parte(intento, asistencia, evaluacion, ahora):
    if intento is not None:
        intento = cerrar_si_vencido(intento, ahora)
        if intento.integridad == OpcionesIntegridad.ANULADO_FRAUDE:
            return 'anulado', intento
        if intento.integridad == OpcionesIntegridad.SUSPENDIDO:
            return 'suspendido', intento
        return ('presento' if intento.enviado else 'en_curso'), intento
    if asistencia is not None and asistencia.estado == 'excusa':
        return 'excusa', None
    if asistencia is not None and asistencia.estado == 'ausente':
        return 'ausente', None
    if ahora <= evaluacion.fecha_fin:
        return 'pendiente', None
    return 'no_presento', None


def _peor(estados, prioridad):
    for e in prioridad:
        if e in estados:
            return e
    return None


# ------------------------------------------------------------------ cálculo

def notas_del_momento(momento) -> dict:
    ahora = timezone.now()
    esquema = esquema_efectivo(momento)
    evaluaciones = list(EvaluacionFormal.objects.filter(
        momento=momento, estado=OpcionesEstadoEvaluacion.PUBLICADA,
    ).select_related('tarea').order_by('fecha_inicio', 'id'))
    cuestionarios = [e for e in evaluaciones if e.tipo == OpcionesTipoEvaluacion.CUESTIONARIO]
    trabajos = [e for e in evaluaciones if e.tipo == OpcionesTipoEvaluacion.TAREA and e.tarea_id]

    convocados_por_ev = {e.id: set(origenes_convocatoria(e)) for e in evaluaciones}
    ids = set().union(*convocados_por_ev.values()) if convocados_por_ev else set()
    preguntas_por_ev = defaultdict(list)
    for ev_id, preg_id in EvaluacionPregunta.objects.filter(evaluacion__in=cuestionarios).values_list(
            'evaluacion_id', 'pregunta_id'):
        preguntas_por_ev[ev_id].append(str(preg_id))
    intentos = {(i.evaluacion_id, i.estudiante_id): i
                for i in IntentoEvaluacion.objects.filter(evaluacion__in=cuestionarios, estudiante_id__in=ids)}
    asistencias = {(a.evaluacion_id, a.estudiante_id): a
                   for a in AsistenciaEvaluacion.objects.filter(evaluacion__in=evaluaciones, estudiante_id__in=ids)}
    entregas = {(e.tarea_id, e.estudiante_id): e
                for e in EntregaTarea.objects.filter(tarea_id__in=[t.tarea_id for t in trabajos], estudiante_id__in=ids)}

    from apps.users.models import User
    estudiantes = list(User.objects.filter(id__in=ids, role__name='Estudiante').select_related(
        'perfil_academico').order_by('first_last_name', 'first_name', 'email'))

    filas, detalle = [], []
    for est in estudiantes:
        # ---- examen
        partes = []
        for ev in cuestionarios:
            if est.id not in convocados_por_ev[ev.id]:
                continue
            estado, intento = _estado_parte(intentos.get((ev.id, est.id)), asistencias.get((ev.id, est.id)), ev, ahora)
            total = len(preguntas_por_ev[ev.id])
            correctas = respondidas = None
            if estado == 'presento':
                total = intento.total if intento.total is not None else total
                correctas = intento.aciertos or 0
                respondidas = sum(1 for q in preguntas_por_ev[ev.id] if intento.respuestas.get(q) is not None)
            partes.append({'evaluacion': ev, 'estado': estado, 'total': total, 'correctas': correctas,
                           'respondidas': respondidas, 'intento': intento,
                           'tipo_excusa': getattr(asistencias.get((ev.id, est.id)), 'tipo_excusa', '')})
            detalle.append({
                'estudiante': est, 'evaluacion': ev.nombre, 'estado': ESTADOS_EXAMEN[estado],
                'correctas': correctas, 'incorrectas': None if correctas is None else respondidas - correctas,
                'sin_responder': None if correctas is None else total - respondidas, 'total': total,
                'nota_sin_redondear': None if correctas is None or not total else _f(Decimal(5) * correctas / total, 2),
                'enviado_en': intento.enviado_en if intento else None,
                'envio_automatico': bool(intento and intento.envio_automatico),
            })
        presentadas = [p for p in partes if p['estado'] == 'presento']
        c = sum(p['correctas'] for p in presentadas)
        r = sum(p['respondidas'] for p in presentadas)
        t = sum(p['total'] for p in presentadas)
        if not partes:
            estado_ex, crudo_ex = 'no_aplica', None
        elif len(presentadas) == len(partes):
            estado_ex = 'presento'
            crudo_ex = Decimal(5) * c / t if t else Decimal(0)
        else:
            estado_ex = _peor({p['estado'] for p in partes}, PRIORIDAD_EXAMEN)
            if presentadas and estado_ex in SIN_EXCUSA_EXAMEN:
                estado_ex = 'incompleto'
            crudo_ex = None
        # Reglamentaria: lo no presentado sin excusa vale 0; si algo está pendiente o justificado, no se determina.
        faltantes = [p for p in partes if p['estado'] != 'presento']
        if partes and all(p['estado'] in SIN_EXCUSA_EXAMEN for p in faltantes):
            total_todo = sum(p['total'] for p in partes)
            regl_ex = Decimal(5) * c / total_todo if total_todo else Decimal(0)
        else:
            regl_ex = None

        # ---- trabajo
        notas_tr, estados_tr = [], []
        for ev in trabajos:
            if est.id not in convocados_por_ev[ev.id]:
                continue
            entrega = entregas.get((ev.tarea_id, est.id))
            if entrega is not None and entrega.nota is not None:
                estados_tr.append(('calificado', entrega))
                notas_tr.append(Decimal(entrega.nota))
            elif entrega is not None:
                estados_tr.append(('pendiente_calificar', entrega))
            elif estado_plazo(ev.tarea, ahora) != 'cerrada':
                estados_tr.append(('pendiente_entrega', None))
            else:
                estados_tr.append(('no_entrego', None))
        if not estados_tr:
            estado_tr, crudo_tr, regl_tr = 'no_aplica', None, None
        elif all(e == 'calificado' for e, _x in estados_tr):
            estado_tr = 'calificado'
            crudo_tr = sum(notas_tr, Decimal(0)) / len(notas_tr)
            regl_tr = crudo_tr
        else:
            estado_tr = _peor({e for e, _x in estados_tr}, PRIORIDAD_TRABAJO)
            if notas_tr and estado_tr == 'no_entrego':
                estado_tr = 'incompleto'
            crudo_tr = None
            no_det = {e for e, _x in estados_tr} & {'pendiente_calificar', 'pendiente_entrega'}
            regl_tr = None if no_det else sum(notas_tr, Decimal(0)) / len(estados_tr)  # no entregado = 0
        con_retraso = any(x is not None and x.con_retraso for _e, x in estados_tr)

        # ---- consolidado
        if estado_tr == 'no_aplica':
            crudo_mo, regl_mo = crudo_ex, regl_ex
            estado_mo = 'calificado' if crudo_ex is not None else 'pendiente'
        elif not esquema['ponderacion_definida']:
            crudo_mo = regl_mo = None
            estado_mo = 'ponderacion_sin_definir'
        else:
            pe, pt = esquema['peso_examen'] / 100, esquema['peso_trabajo'] / 100
            crudo_mo = pe * crudo_ex + pt * crudo_tr if crudo_ex is not None and crudo_tr is not None else None
            regl_mo = pe * regl_ex + pt * regl_tr if regl_ex is not None and regl_tr is not None else None
            estado_mo = 'calificado' if crudo_mo is not None else 'pendiente'

        nota_ex, nota_tr, nota_mo = redondear(crudo_ex), redondear(crudo_tr), redondear(crudo_mo)
        regl = redondear(regl_mo)
        peso_m, peso_c = esquema['peso_momento_en_corte'], esquema['peso_corte_en_definitiva']
        aporte_corte = nota_mo * peso_m / 100 if nota_mo is not None and peso_m is not None else None
        aporte_def = aporte_corte * peso_c / 100 if aporte_corte is not None and peso_c is not None else None
        perfil = getattr(est, 'perfil_academico', None)
        excusa = next((p['tipo_excusa'] for p in partes if p['estado'] == 'excusa' and p['tipo_excusa']), '')
        filas.append({
            'estudiante_id': est.id,
            'codigo': perfil.codigo_matricula if perfil else '',
            'nombre': nombre_completo(est), 'correo': est.email,
            'examen': {
                'nota': _f(nota_ex), 'nivel': nivel(nota_ex), 'estado': estado_ex,
                'estado_texto': ESTADOS_EXAMEN[estado_ex] + (f' ({len(presentadas)} de {len(partes)} partes)'
                                                             if estado_ex == 'incompleto' else ''),
                'correctas': c if presentadas else None, 'incorrectas': r - c if presentadas else None,
                'sin_responder': t - r if presentadas else None, 'total': t if presentadas else None,
                'porcentaje': _f(Decimal(100) * c / t) if presentadas and t else None,
                'partes': len(partes), 'partes_presentadas': len(presentadas), 'tipo_excusa': excusa,
            },
            'trabajo': {
                'nota': _f(nota_tr), 'nivel': nivel(nota_tr), 'estado': estado_tr,
                'estado_texto': ESTADOS_TRABAJO[estado_tr] + (' · con retraso' if con_retraso else ''),
                'cantidad': len(estados_tr),
            },
            'momento': {
                'nota': _f(nota_mo), 'nivel': nivel(nota_mo), 'aprueba': aprueba(nota_mo), 'estado': estado_mo,
                'estado_texto': ESTADOS_CONSOLIDADO[estado_mo],
                'nota_reglamentaria': _f(regl),
                'aporte_tercer_corte': _f(aporte_corte, 2), 'aporte_definitiva': _f(aporte_def, 2),
            },
        })

    abiertas = any(ahora <= e.fecha_fin for e in evaluaciones)
    provisional = abiertas or any(
        f['examen']['estado'] in ('en_curso', 'suspendido', 'pendiente')
        or f['trabajo']['estado'] in ('pendiente_calificar', 'pendiente_entrega')
        or f['momento']['estado'] == 'ponderacion_sin_definir' for f in filas)
    return {
        'momento': {'id': momento.id, 'nombre': momento.nombre, 'periodo': momento.periodo,
                    'programa': f'{momento.programa.codigo} · {momento.programa.nombre}',
                    'semestre_referencia': momento.semestre_referencia},
        'generado_en': timezone.localtime(ahora),
        'esquema': {k: (_f(v, 2) if isinstance(v, Decimal) else v) for k, v in esquema.items()},
        'evaluaciones': [{'id': e.id, 'nombre': e.nombre, 'tipo': e.tipo, 'fecha_fin': e.fecha_fin,
                          'preguntas': len(preguntas_por_ev.get(e.id, [])) if e.tipo == 'cuestionario' else None}
                         for e in evaluaciones],
        'tiene_trabajo': bool(trabajos),
        'provisional': provisional,
        'filas': filas,
        'detalle': [{**d, 'estudiante': nombre_completo(d['estudiante']), 'correo': d['estudiante'].email}
                    for d in detalle],
        'resumen': resumen(filas),
        'fuentes': FUENTES,
    }


# ------------------------------------------------------------------ resumen

def _promedio(valores):
    valores = [Decimal(str(v)) for v in valores if v is not None]
    return _f(sum(valores) / len(valores), 2) if valores else None


def resumen(filas) -> dict:
    n = len(filas)
    ex = [f['examen'] for f in filas if f['examen']['estado'] != 'no_aplica']
    cuenta = defaultdict(int)
    for e in ex:
        cuenta[e['estado']] += 1
    pct = lambda x, d: _f(Decimal(100) * x / d) if d else None  # noqa: E731
    momentos = [f['momento']['nota'] for f in filas if f['momento']['nota'] is not None]
    niveles = defaultdict(int)
    for v in momentos:
        niveles[nivel(v)] += 1
    aprobados = sum(1 for v in momentos if aprueba(v))
    promedio_mo = _promedio(momentos)
    return {
        'convocados': n,
        'examen': {
            'convocados': len(ex), 'presentaron': cuenta['presento'], 'pct_presentaron': pct(cuenta['presento'], len(ex)),
            'ausentes': cuenta['ausente'] + cuenta['no_presento'],
            'pct_ausentes': pct(cuenta['ausente'] + cuenta['no_presento'], len(ex)),
            'con_excusa': cuenta['excusa'], 'anulados': cuenta['anulado'], 'incompletos': cuenta['incompleto'],
            'en_curso_o_pendientes': cuenta['en_curso'] + cuenta['pendiente'] + cuenta['suspendido'],
            'promedio': _promedio(f['examen']['nota'] for f in filas),
        },
        'trabajo': {'promedio': _promedio(f['trabajo']['nota'] for f in filas),
                    'calificados': sum(1 for f in filas if f['trabajo']['estado'] == 'calificado')},
        'momento': {
            'con_nota': len(momentos), 'promedio': promedio_mo,
            'niveles': [{'clave': c, 'etiqueta': e, 'cantidad': niveles[c], 'porcentaje': pct(niveles[c], len(momentos))}
                        for c, e, _m in NIVELES],
            'aprobados': aprobados, 'pct_aprobacion': pct(aprobados, len(momentos)),
            'meta_aprobacion': _f(META_APROBACION_PCT), 'meta_promedio': _f(META_PROMEDIO),
            'cumple_aprobacion': None if not momentos else Decimal(100) * aprobados / len(momentos) >= META_APROBACION_PCT,
            'cumple_promedio': None if promedio_mo is None else Decimal(str(promedio_mo)) >= META_PROMEDIO,
        },
        'nota_aprobacion': _f(NOTA_APROBACION),
        'etiquetas_nivel': ETIQUETA_NIVEL,
    }
