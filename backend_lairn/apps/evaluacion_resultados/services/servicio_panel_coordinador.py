"""
Panel de inicio del Coordinador (ADR-013), con datos reales de sus programas.

Reutiliza las agregaciones de la analítica de RA (ADR-011) para no duplicar
reglas: cobertura de RA obligatorios, estado de evaluaciones, convocatoria y
participación, alertas e integridad. Añade lo propio del día a día del
Coordinador: próximas evaluaciones, preguntas pendientes de validación por
asignatura (las valida el docente, HU-05), docentes con cursos vinculados y
estudiantes suspendidos que esperan decisión.

No expone nada que hoy sea solo del Administrador (crear programas,
importación, desempeño por RA de HU-09.1).
Sin datos = listas vacías o ceros reales; nunca valores inventados.
"""

from collections import defaultdict

from django.db.models import Count, Q
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    AsignaturaMalla,
    EvaluacionFormal,
    IntentoEvaluacion,
    OpcionesEstadoAlerta,
    OpcionesEstadoEvaluacion,
    OpcionesEstadoPregunta,
    OpcionesIntegridad,
    PreguntaBanco,
    ProgramaAcademico,
)

from .servicio_analitica_ra import (
    Filtros,
    _alertas,
    _cobertura,
    _estado_evaluaciones,
    _integridad,
    _participacion,
    cerrar_vencidos,
)
from .servicio_supervision import nombre_completo

MAX_PROXIMAS, MAX_ALERTAS = 8, 5


def _proximas(programa_id):
    ahora = timezone.now()
    qs = EvaluacionFormal.objects.filter(
        estado=OpcionesEstadoEvaluacion.PUBLICADA, fecha_fin__gte=ahora,
    ).select_related('momento__programa', 'supervisor').order_by('fecha_inicio')
    if programa_id:
        qs = qs.filter(momento__programa_id=programa_id)
    return [
        {'id': e.id, 'nombre': e.nombre, 'tipo': e.tipo, 'momento_id': e.momento_id, 'momento': e.momento.nombre,
         'programa': e.momento.programa.codigo, 'fecha_inicio': e.fecha_inicio, 'fecha_fin': e.fecha_fin,
         'abierta': e.fecha_inicio <= ahora, 'duracion_minutos': e.duracion_minutos,
         'supervisor': nombre_completo(e.supervisor) if e.supervisor_id else None}
        for e in qs[:MAX_PROXIMAS]
    ]


def _momentos(programa_id, cobertura):
    """Cobertura de cada momento + cuántas evaluaciones tiene por estado."""
    por_momento = defaultdict(lambda: {'borradores': 0, 'publicadas': 0})
    qs = EvaluacionFormal.objects.all()
    if programa_id:
        qs = qs.filter(momento__programa_id=programa_id)
    for momento_id, estado, total in qs.values_list('momento_id', 'estado').annotate(n=Count('id')):
        clave = 'publicadas' if estado == OpcionesEstadoEvaluacion.PUBLICADA else 'borradores'
        por_momento[momento_id][clave] += total
    return [{**c, **por_momento[c['momento']]} for c in cobertura]


def _alertas_recientes(programa_id):
    qs = AlertaDesempeno.objects.filter(estado=OpcionesEstadoAlerta.ABIERTA).select_related(
        'estudiante', 'asignatura', 'programa').order_by('-actividades_bajas', '-id')
    if programa_id:
        qs = qs.filter(programa_id=programa_id)
    return [
        {'id': a.id, 'tipo': a.tipo, 'programa': a.programa.codigo,
         'estudiante': nombre_completo(a.estudiante) if a.estudiante_id else None,
         'asignatura': f'{a.asignatura.codigo} · {a.asignatura.nombre}' if a.asignatura_id else None,
         'actividades_bajas': a.actividades_bajas, 'total_actividades': a.total_actividades}
        for a in qs[:MAX_ALERTAS]
    ]


def _banco(programa_id):
    qs = PreguntaBanco.objects.all()
    if programa_id:
        qs = qs.filter(asignatura__programa_id=programa_id)
    filas = list(
        qs.values('asignatura_id', 'asignatura__codigo', 'asignatura__nombre').annotate(
            pendientes=Count('id', filter=Q(estado=OpcionesEstadoPregunta.PENDIENTE)),
            aprobadas=Count('id', filter=Q(estado=OpcionesEstadoPregunta.APROBADA)),
        ).filter(Q(pendientes__gt=0) | Q(aprobadas__gt=0)).order_by('-pendientes', 'asignatura__codigo')
    )
    return {
        'pendientes': sum(f['pendientes'] for f in filas),
        'aprobadas': sum(f['aprobadas'] for f in filas),
        'por_asignatura': [
            {'asignatura': f['asignatura_id'], 'codigo': f['asignatura__codigo'], 'nombre': f['asignatura__nombre'],
             'pendientes': f['pendientes'], 'aprobadas': f['aprobadas']}
            for f in filas
        ],
    }


def _docentes(programa_id):
    asignaturas = AsignaturaMalla.objects.filter(activo=True)
    if programa_id:
        asignaturas = asignaturas.filter(programa_id=programa_id)
    sin_curso = asignaturas.filter(curso_vinculado__isnull=True).count()
    grupos = {}
    for a in asignaturas.filter(curso_vinculado__isnull=False).select_related('curso_vinculado__docente'):
        docente = a.curso_vinculado.docente
        g = grupos.setdefault(docente.id, {'id': docente.id, 'nombre': nombre_completo(docente), 'email': docente.email,
                                           'asignaturas': [], 'cursos': set()})
        g['asignaturas'].append(a.codigo)
        g['cursos'].add(a.curso_vinculado_id)
    docentes = sorted(
        ({**g, 'cursos': len(g['cursos']), 'asignaturas': sorted(g['asignaturas'])} for g in grupos.values()),
        key=lambda d: d['nombre'].lower(),
    )
    return {'docentes': docentes, 'asignaturas_sin_curso': sin_curso,
            'asignaturas_con_curso': asignaturas.count() - sin_curso}


def _suspendidos(programa_id):
    qs = IntentoEvaluacion.objects.filter(integridad=OpcionesIntegridad.SUSPENDIDO).select_related(
        'estudiante', 'evaluacion__momento', 'evaluacion__supervisor').order_by('suspendido_en')
    if programa_id:
        qs = qs.filter(evaluacion__momento__programa_id=programa_id)
    return [
        {'estudiante': nombre_completo(i.estudiante), 'evaluacion': i.evaluacion_id, 'nombre': i.evaluacion.nombre,
         'momento_id': i.evaluacion.momento_id, 'suspendido_en': i.suspendido_en,
         'decide': (nombre_completo(i.evaluacion.supervisor) if i.evaluacion.supervisor_id
                    else 'Coordinador o Administrador')}
        for i in qs
    ]


def panel(programa_id=None) -> dict:
    cerrar_vencidos()
    f = Filtros(programa=programa_id)
    cobertura = _cobertura(f)
    return {
        'programa': programa_id,
        'programas': [{'id': p.id, 'nombre': f'{p.codigo} · {p.nombre}'}
                      for p in ProgramaAcademico.objects.filter(activo=True).order_by('codigo')],
        'generado_en': timezone.now(),
        'momentos': _momentos(programa_id, cobertura),
        'evaluaciones': _estado_evaluaciones(f),
        'proximas': _proximas(programa_id),
        'participacion': _participacion(f)['resumen'],
        'alertas': {**_alertas(f), 'recientes': _alertas_recientes(programa_id)},
        'banco': _banco(programa_id),
        'docentes': _docentes(programa_id),
        'integridad': {**_integridad(f), 'suspendidos': _suspendidos(programa_id)},
    }
