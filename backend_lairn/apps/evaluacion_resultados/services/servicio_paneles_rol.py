"""
Resúmenes de inicio por rol (ADR-014): Administrador, Docente y Estudiante.

Reutiliza lo que ya existe (no duplica reglas):
  - convocatoria y presentación: `servicio_presentacion` (HU-07, ADR-009);
  - analítica de RA con métrica provisional: `servicio_analitica_ra` (ADR-011);
  - estado de evaluaciones, suspendidos e integridad: ADR-010/011/013;
  - alcance del docente: `asignaturas_del_docente` / `tareas_del_docente`;
  - tareas del estudiante: `tareas_del_estudiante` y `estado_plazo` (HU-08).

Reglas del backlog que se respetan:
  - HU-07: el estudiante NO ve la nota de la evaluación formal; sí ve la nota
    de sus tareas calificadas (HU-08A).
  - Docente: resultados agregados por RA y por pregunta solo de SUS
    asignaturas (sin datos por estudiante) y con el aviso de métrica provisional.
"""

from collections import defaultdict

from django.db.models import Count, Q
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    AsistenciaEvaluacion,
    CargueDocumental,
    ConvocadoEvaluacion,
    EntregaTarea,
    EvaluacionFormal,
    IntentoEvaluacion,
    OpcionesEstadoAlerta,
    OpcionesEstadoEvaluacion,
    OpcionesEstadoTarea,
    OpcionesIntegridad,
    PreguntaBanco,
    RegistroSincronizacion,
)

from .servicio_analitica_ra import (
    Filtros,
    _acumular,
    _estado_evaluaciones,
    _integridad,
    _medida,
    cerrar_vencidos,
    observaciones,
)
from .servicio_desempeno_ra import METRICA_PROVISIONAL
from .servicio_panel_coordinador import _proximas, _suspendidos
from .servicio_presentacion import esta_activa, evaluaciones_convocadas
from .servicio_supervision import nombre_completo
from .servicio_tareas import estado_plazo

MAX_LISTA = 5


# ------------------------------------------------------------------ Administrador

def panel_admin() -> dict:
    from apps.users.models import User

    cerrar_vencidos()
    usuarios = defaultdict(lambda: {'activos': 0, 'inactivos': 0})
    for rol, activo, n in User.objects.values_list('role__name', 'is_active').annotate(total=Count('id')):
        usuarios[rol or 'Sin rol']['activos' if activo else 'inactivos'] += n
    cargues = CargueDocumental.objects.select_related('programa').order_by('-creado_en')
    return {
        'generado_en': timezone.now(),
        'usuarios': [{'rol': rol, **v} for rol, v in sorted(usuarios.items())],
        'importaciones': [
            {'id': r.id, 'creado_en': r.creado_en, 'origen': r.origen, 'entidad': r.entidad, 'modo': r.modo,
             'recibidos': r.total_recibidos, 'creados': r.creados, 'actualizados': r.actualizados,
             'omitidos': r.omitidos, 'errores': len(r.errores or []),
             'ejecutado_por': nombre_completo(r.ejecutado_por) if r.ejecutado_por_id else None}
            for r in RegistroSincronizacion.objects.select_related('ejecutado_por').order_by('-creado_en')[:MAX_LISTA]
        ],
        'cargues': {
            'por_estado': dict(CargueDocumental.objects.values_list('estado').annotate(n=Count('id'))),
            'recientes': [
                {'id': c.id, 'nombre_archivo': c.nombre_archivo, 'tipo': c.tipo, 'estado': c.estado,
                 'programa': c.programa.codigo if c.programa_id else None, 'creado_en': c.creado_en}
                for c in cargues[:MAX_LISTA]
            ],
        },
        'evaluaciones': _estado_evaluaciones(Filtros()),
        'abiertas': [e for e in _proximas(None) if e['abierta']],
        'convocados_por_cargue': ConvocadoEvaluacion.objects.count(),
        'alertas_abiertas': AlertaDesempeno.objects.filter(estado=OpcionesEstadoAlerta.ABIERTA).count(),
        'integridad': {**_integridad(Filtros()), 'suspendidos': _suspendidos(None)},
    }


# ------------------------------------------------------------------------ Docente

def panel_docente(usuario) -> dict:
    from apps.evaluacion_resultados.views.docente.vista_banco_preguntas import asignaturas_del_docente
    from apps.evaluacion_resultados.views.docente.vista_tareas import tareas_del_docente

    cerrar_vencidos()
    ahora = timezone.now()
    asignaturas = list(asignaturas_del_docente(usuario).select_related('curso_vinculado'))
    ids = [a.id for a in asignaturas]

    banco = defaultdict(lambda: {'pendiente': 0, 'aprobada': 0, 'descartada': 0})
    for asig_id, estado, n in PreguntaBanco.objects.filter(asignatura_id__in=ids).values_list(
            'asignatura_id', 'estado').annotate(total=Count('id')):
        banco[asig_id][estado] = n

    tareas = tareas_del_docente(usuario)
    sin_calificar = EntregaTarea.objects.filter(tarea__in=tareas, nota__isnull=True).count()
    proximas_tareas = [
        {'id': t.id, 'titulo': t.titulo, 'asignatura': t.asignatura.codigo, 'fecha_limite': t.fecha_limite,
         'entregas': t.n_entregas, 'sin_calificar': t.n_sin_calificar}
        for t in tareas.filter(estado=OpcionesEstadoTarea.PUBLICADA, fecha_limite__gte=ahora)
        .select_related('asignatura').annotate(
            n_entregas=Count('entregas', distinct=True),
            n_sin_calificar=Count('entregas', filter=Q(entregas__nota__isnull=True), distinct=True),
        ).order_by('fecha_limite')[:MAX_LISTA]
    ]

    supervisiones = [
        {'id': e.id, 'nombre': e.nombre, 'momento': e.momento.nombre, 'fecha_inicio': e.fecha_inicio,
         'fecha_fin': e.fecha_fin, 'abierta': e.fecha_inicio <= ahora}
        for e in EvaluacionFormal.objects.filter(
            supervisor=usuario, estado=OpcionesEstadoEvaluacion.PUBLICADA, fecha_fin__gte=ahora,
        ).select_related('momento').order_by('fecha_inicio')[:MAX_LISTA]
    ]

    # Resultados agregados de SUS asignaturas (métrica provisional, sin datos por estudiante).
    obs = observaciones(Filtros(docente=usuario.id)) if ids else []
    por_ra = _acumular(obs, lambda o: o.resultado.id)
    info = {o.resultado.id: (o.resultado.descripcion, o.asignatura.codigo) for o in obs}
    por_pregunta = _acumular(obs, lambda o: o.pregunta.id)
    preguntas = {o.pregunta.id: o for o in obs}
    total = _acumular(obs, lambda o: 'total').get('total') if obs else None

    return {
        'generado_en': ahora,
        'asignaturas': [
            {'id': a.id, 'codigo': a.codigo, 'nombre': a.nombre, 'curso': a.curso_vinculado.nombre,
             'preguntas': banco[a.id]}
            for a in asignaturas
        ],
        'banco': {e: sum(b[e] for b in banco.values()) for e in ('pendiente', 'aprobada', 'descartada')},
        'tareas': {
            'borradores': tareas.filter(estado=OpcionesEstadoTarea.BORRADOR).count(),
            'publicadas': tareas.filter(estado=OpcionesEstadoTarea.PUBLICADA).count(),
            'entregas_sin_calificar': sin_calificar,
            'proximas': proximas_tareas,
        },
        'supervisiones': supervisiones,
        'resultados': {
            'aviso': 'Métrica provisional: pendiente de definición con Vicerrectoría (ADR-006).',
            'umbral_logro_porcentaje': METRICA_PROVISIONAL['umbral_logro_porcentaje'],
            'general': _medida(total) if total else None,
            'por_ra': sorted(
                ({'id': r, 'descripcion': info[r][0], 'asignatura': info[r][1], **_medida(g)} for r, g in por_ra.items()),
                key=lambda x: (x['porcentaje'] if x['porcentaje'] is not None else 101),
            ),
            'preguntas_error': sorted(
                ({'pregunta': p, 'enunciado': preguntas[p].pregunta.enunciado[:160],
                  'asignatura': preguntas[p].asignatura.codigo, 'presentadas': g['presentadas'],
                  'porcentaje_error': round(100 * (g['presentadas'] - g['aciertos']) / g['presentadas'], 1)}
                 for p, g in por_pregunta.items()),
                key=lambda x: (-x['porcentaje_error'], -x['presentadas']),
            )[:MAX_LISTA],
        },
    }


# --------------------------------------------------------------------- Estudiante

def panel_estudiante(usuario) -> dict:
    from apps.evaluacion_resultados.views.estudiante.vista_tareas_estudiante import tareas_del_estudiante

    ahora = timezone.now()
    convocadas = list(evaluaciones_convocadas(usuario).filter(fecha_fin__gte=ahora).order_by('fecha_inicio'))
    intentos = {i.evaluacion_id: i for i in IntentoEvaluacion.objects.filter(estudiante=usuario)}
    asistencias = dict(AsistenciaEvaluacion.objects.filter(estudiante=usuario).values_list('evaluacion_id', 'estado'))
    pendientes_eval = []
    for e in convocadas:
        intento = intentos.get(e.id)
        if intento is not None and intento.enviado:
            continue
        pendientes_eval.append({
            'id': e.id, 'nombre': e.nombre, 'tipo': e.tipo, 'momento': e.momento.nombre,
            'fecha_inicio': e.fecha_inicio, 'fecha_fin': e.fecha_fin, 'activa': esta_activa(e, ahora),
            'duracion_minutos': e.duracion_minutos,
            'requiere_asistencia': bool(e.supervisor_id), 'asistencia': asistencias.get(e.id),
            'intento': None if intento is None else ('suspendido' if intento.suspendido else 'en_curso'),
            'tarea': e.tarea_id,
        })

    entregas = {en.tarea_id: en for en in EntregaTarea.objects.filter(estudiante=usuario).select_related('tarea__asignatura')}
    tareas = list(tareas_del_estudiante(usuario).order_by('fecha_limite'))
    pendientes_tareas = [
        {'id': t.id, 'titulo': t.titulo, 'asignatura': t.asignatura.codigo, 'fecha_limite': t.fecha_limite,
         'plazo': estado_plazo(t, ahora)}
        for t in tareas if t.id not in entregas and estado_plazo(t, ahora) != 'cerrada'
    ]

    presentadas = [
        # HU-07: sin nota de la evaluación formal.
        {'id': i.evaluacion_id, 'nombre': i.evaluacion.nombre, 'momento': i.evaluacion.momento.nombre,
         'enviado_en': i.enviado_en, 'envio_automatico': i.envio_automatico,
         'anulada': i.integridad == OpcionesIntegridad.ANULADO_FRAUDE}
        for i in IntentoEvaluacion.objects.filter(estudiante=usuario, enviado_en__isnull=False)
        .select_related('evaluacion__momento').order_by('-enviado_en')[:MAX_LISTA * 2]
    ]
    entregadas = [
        # HU-08A: la nota de la tarea sí se muestra al estudiante.
        {'id': en.tarea_id, 'titulo': en.tarea.titulo, 'asignatura': en.tarea.asignatura.codigo,
         'enviada_en': en.enviada_en, 'con_retraso': en.con_retraso,
         'nota': en.nota, 'calificada': en.nota is not None}
        for en in sorted(entregas.values(), key=lambda x: x.enviada_en, reverse=True)[:MAX_LISTA * 2]
    ]
    return {
        'generado_en': ahora,
        'pendientes': {'evaluaciones': pendientes_eval, 'tareas': pendientes_tareas},
        'historial': {'evaluaciones': presentadas, 'tareas': entregadas},
        'resumen': {
            'evaluaciones_pendientes': len(pendientes_eval),
            'tareas_pendientes': len(pendientes_tareas),
            'evaluaciones_presentadas': IntentoEvaluacion.objects.filter(estudiante=usuario, enviado_en__isnull=False).count(),
            'tareas_entregadas': len(entregas),
        },
    }
