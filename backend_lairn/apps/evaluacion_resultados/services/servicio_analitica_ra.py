"""
Analítica de evaluación de resultados de aprendizaje para Vicerrectoría (ADR-011).

Responde: ¿qué RA y competencias se están logrando, dónde, en qué momentos y
con qué tendencia? Amplía el reporte ejecutivo (HU-11) en `/reporte-institucional`.

Base de cálculo: "observaciones" = cada pregunta presentada en un intento
ENVIADO y no anulado por fraude de una evaluación formal tipo cuestionario.
Si es acierto o no lo decide la métrica PROVISIONAL de `servicio_desempeno_ra`
(único lugar configurable). Las tareas calificadas entran solo en las notas 0-5.

Rendimiento: un número fijo de consultas, sin importar cuántos intentos haya
(los JSON de respuestas se comparan en Python; ver pruebas con conteo).

Filtros: programa, semestre (número), momento, desde/hasta (fecha), asignatura,
docente (dueño del curso vinculado), competencia, resultado (RA), evaluación.
Una celda sin observaciones NO es 0: no aparece y la UI la marca "sin datos".
"""

from collections import defaultdict
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    AsignaturaMalla,
    AsistenciaEvaluacion,
    Competencia,
    ConvocadoEvaluacion,
    EntregaTarea,
    EvaluacionFormal,
    EvaluacionPregunta,
    IncidenteIntento,
    IntentoEvaluacion,
    MomentoEvaluacion,
    MomentoResultado,
    OpcionesAccionIntegridad,
    OpcionesConsecuencia,
    OpcionesEstadoAlerta,
    OpcionesEstadoEvaluacion,
    OpcionesIntegridad,
    OpcionesTipoEvaluacion,
    ProgramaAcademico,
    ResolucionIntegridad,
    ResultadoAprendizaje,
)

from .servicio_desempeno_ra import (
    METRICA_PROVISIONAL,
    evaluar_respuesta,
    nivel_de_nota,
    porcentaje,
    ra_logrado,
)
from .servicio_presentacion import GRACIA_SEGUNDOS, cerrar_si_vencido

ESTADOS_PRESENTE = {'presente', 'tarde'}
# El proyecto corre en UTC (settings.TIME_ZONE); las fechas del reporte (filtros
# desde/hasta y fecha de corte) se interpretan en la hora de la institución.
ZONA_INSTITUCIONAL = ZoneInfo('America/Bogota')
TOP_PREGUNTAS_ERROR = 10
MAX_SERIES_TENDENCIA = 6


# --------------------------------------------------------------------- filtros

@dataclass
class Filtros:
    programa: int | None = None
    semestre: int | None = None
    momento: int | None = None
    desde: date | None = None
    hasta: date | None = None
    asignatura: int | None = None
    docente: int | None = None
    competencia: int | None = None
    resultado: int | None = None
    evaluacion: int | None = None

    def aplicados(self) -> dict:
        return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in asdict(self).items() if v is not None}

    @property
    def filtra_preguntas(self) -> bool:
        return any(getattr(self, k) for k in ('semestre', 'asignatura', 'docente', 'competencia', 'resultado'))


def leer_filtros(params) -> Filtros:
    """Lee los filtros de la URL. Lanza ValueError con un mensaje legible si alguno es inválido."""
    datos = {}
    for campo in fields(Filtros):
        valor = (params.get(campo.name) or '').strip()
        if not valor:
            continue
        if campo.name in ('desde', 'hasta'):
            try:
                datos[campo.name] = date.fromisoformat(valor)
            except ValueError as exc:
                raise ValueError(f'La fecha "{campo.name}" debe tener el formato AAAA-MM-DD.') from exc
        else:
            if not valor.isdigit():
                raise ValueError(f'El filtro "{campo.name}" debe ser un número.')
            datos[campo.name] = int(valor)
    filtros = Filtros(**datos)
    if filtros.desde and filtros.hasta and filtros.desde > filtros.hasta:
        raise ValueError('La fecha "desde" no puede ser posterior a "hasta".')
    return filtros


def _rango(f: Filtros):
    zona = ZONA_INSTITUCIONAL
    inicio = datetime.combine(f.desde, time.min, zona) if f.desde else None
    fin = datetime.combine(f.hasta + timedelta(days=1), time.min, zona) if f.hasta else None
    return inicio, fin


def _pregunta_pasa(p, f: Filtros) -> bool:
    a = p.asignatura
    if f.asignatura and a.id != f.asignatura:
        return False
    if f.semestre and (a.semestre is None or a.semestre.numero != f.semestre):
        return False
    if f.docente and (a.curso_vinculado is None or a.curso_vinculado.docente_id != f.docente):
        return False
    if f.resultado and p.resultado_id != f.resultado:
        return False
    if f.competencia and p.resultado.competencia_id != f.competencia:
        return False
    return True


def _evaluaciones_base(f: Filtros):
    qs = EvaluacionFormal.objects.all()
    if f.programa:
        qs = qs.filter(momento__programa_id=f.programa)
    if f.momento:
        qs = qs.filter(momento_id=f.momento)
    if f.evaluacion:
        qs = qs.filter(id=f.evaluacion)
    inicio, fin = _rango(f)
    if inicio:
        qs = qs.filter(fecha_fin__gte=inicio)
    if fin:
        qs = qs.filter(fecha_inicio__lt=fin)
    if f.filtra_preguntas:
        # Una evaluación entra si alguna de sus preguntas (o su tarea) cumple los filtros de la malla.
        q_preg = Q()
        q_tarea = Q()
        if f.asignatura:
            q_preg &= Q(items__pregunta__asignatura_id=f.asignatura)
            q_tarea &= Q(tarea__asignatura_id=f.asignatura)
        if f.semestre:
            q_preg &= Q(items__pregunta__asignatura__semestre__numero=f.semestre)
            q_tarea &= Q(tarea__asignatura__semestre__numero=f.semestre)
        if f.docente:
            q_preg &= Q(items__pregunta__asignatura__curso_vinculado__docente_id=f.docente)
            q_tarea &= Q(tarea__asignatura__curso_vinculado__docente_id=f.docente)
        if f.resultado:
            q_preg &= Q(items__pregunta__resultado_id=f.resultado)
            q_tarea &= Q(tarea__resultado_id=f.resultado)
        if f.competencia:
            q_preg &= Q(items__pregunta__resultado__competencia_id=f.competencia)
            q_tarea &= Q(tarea__resultado__competencia_id=f.competencia)
        qs = qs.filter(q_preg | q_tarea).distinct()
    return qs


# ---------------------------------------------------------------- observaciones

@dataclass
class Observacion:
    estudiante: int
    intento: int
    evaluacion: object
    momento: object
    programa: object
    pregunta: object
    resultado: object
    competencia: object
    asignatura: object
    semestre: int | None
    curso_id: int | None
    acierto: bool


def cerrar_vencidos():
    """Intentos vencidos sin abrir: envío automático (HU-07.3) antes de contar."""
    for intento in IntentoEvaluacion.objects.filter(
        enviado_en__isnull=True, vence_en__lt=timezone.now() - timedelta(seconds=GRACIA_SEGUNDOS),
    ).exclude(integridad=OpcionesIntegridad.SUSPENDIDO):
        cerrar_si_vencido(intento)


def observaciones(f: Filtros) -> list:
    intentos = IntentoEvaluacion.objects.filter(
        enviado_en__isnull=False, evaluacion__tipo=OpcionesTipoEvaluacion.CUESTIONARIO,
        evaluacion__in=_evaluaciones_base(f),
    ).exclude(integridad=OpcionesIntegridad.ANULADO_FRAUDE).select_related('evaluacion__momento__programa')
    inicio, fin = _rango(f)
    if inicio:
        intentos = intentos.filter(enviado_en__gte=inicio)
    if fin:
        intentos = intentos.filter(enviado_en__lt=fin)
    intentos = list(intentos)
    preguntas = defaultdict(list)
    for item in EvaluacionPregunta.objects.filter(
        evaluacion_id__in={i.evaluacion_id for i in intentos},
    ).select_related(
        'pregunta__resultado__competencia', 'pregunta__asignatura__semestre',
        'pregunta__asignatura__curso_vinculado',
    ):
        if _pregunta_pasa(item.pregunta, f):
            preguntas[item.evaluacion_id].append(item.pregunta)
    resultado = []
    for intento in intentos:
        evaluacion = intento.evaluacion
        for p in preguntas[intento.evaluacion_id]:
            acierto = evaluar_respuesta(intento.respuestas, p)
            if acierto is None:
                continue
            a = p.asignatura
            resultado.append(Observacion(
                estudiante=intento.estudiante_id, intento=intento.id, evaluacion=evaluacion,
                momento=evaluacion.momento, programa=evaluacion.momento.programa, pregunta=p,
                resultado=p.resultado, competencia=p.resultado.competencia, asignatura=a,
                semestre=a.semestre.numero if a.semestre_id else None,
                curso_id=a.curso_vinculado_id, acierto=acierto,
            ))
    return resultado


def _acumular(obs, clave):
    grupos = defaultdict(lambda: {'aciertos': 0, 'presentadas': 0, 'estudiantes': set()})
    for o in obs:
        g = grupos[clave(o)]
        g['presentadas'] += 1
        g['aciertos'] += int(o.acierto)
        g['estudiantes'].add(o.estudiante)
    return grupos


def _medida(g) -> dict:
    pct = porcentaje(g['aciertos'], g['presentadas'])
    return {'porcentaje': pct, 'aciertos': g['aciertos'], 'presentadas': g['presentadas'],
            'estudiantes': len(g['estudiantes']), 'logrado': ra_logrado(pct)}


# -------------------------------------------------------------------- notas 0-5

def notas(f: Filtros, obs=None) -> list:
    """Filas {estudiante, programa, asignatura, nota}: una por (intento, asignatura) y por entrega calificada."""
    obs = observaciones(f) if obs is None else obs
    por_intento = defaultdict(lambda: [0, 0, None, None])
    for o in obs:
        acumulado = por_intento[(o.intento, o.asignatura.id)]
        acumulado[0] += int(o.acierto)
        acumulado[1] += 1
        acumulado[2] = o
        acumulado[3] = o.asignatura
    filas = [
        {'estudiante': o.estudiante, 'programa': o.programa, 'asignatura': asig, 'nota': round(5 * a / t, 2)}
        for a, t, o, asig in por_intento.values()
    ]
    entregas = EntregaTarea.objects.filter(
        nota__isnull=False,
        tarea__evaluaciones_formales__in=_evaluaciones_base(f).filter(
            tipo=OpcionesTipoEvaluacion.TAREA, estado=OpcionesEstadoEvaluacion.PUBLICADA,
        ),
    ).select_related('tarea__asignatura__semestre', 'tarea__asignatura__curso_vinculado',
                     'tarea__asignatura__programa', 'tarea__resultado__competencia')
    inicio, fin = _rango(f)
    if inicio:
        entregas = entregas.filter(calificada_en__gte=inicio)
    if fin:
        entregas = entregas.filter(calificada_en__lt=fin)
    for e in entregas.distinct():
        a = e.tarea.asignatura
        if f.asignatura and a.id != f.asignatura:
            continue
        if f.semestre and (a.semestre is None or a.semestre.numero != f.semestre):
            continue
        if f.docente and (a.curso_vinculado is None or a.curso_vinculado.docente_id != f.docente):
            continue
        if f.resultado and e.tarea.resultado_id != f.resultado:
            continue
        if f.competencia and (e.tarea.resultado is None or e.tarea.resultado.competencia_id != f.competencia):
            continue
        filas.append({'estudiante': e.estudiante_id, 'programa': a.programa, 'asignatura': a, 'nota': float(e.nota)})
    return filas


def niveles(filas) -> dict:
    """Distribución por niveles de desempeño (provisional) y % de aprobación."""
    conteo = defaultdict(int)
    for fila in filas:
        conteo[nivel_de_nota(fila['nota'])] += 1
    total = len(filas)
    lista = [
        {'clave': clave, 'etiqueta': etiqueta, 'minimo': minimo, 'cantidad': conteo[clave],
         'porcentaje': porcentaje(conteo[clave], total)}
        for clave, etiqueta, minimo in METRICA_PROVISIONAL['niveles']
    ]
    aprobados = sum(conteo[c] for c in METRICA_PROVISIONAL['niveles_aprobados'])
    return {'niveles': lista, 'total': total, 'aprobacion': porcentaje(aprobados, total)}


# ------------------------------------------------------------- otras secciones

def _contexto(f: Filtros) -> dict:
    from apps.examenes.models import Curso
    from apps.users.models import User

    usuarios = dict(
        User.objects.filter(is_active=True, role__isnull=False).values_list('role__name').annotate(n=Count('id'))
    )
    asignaturas = AsignaturaMalla.objects.filter(activo=True)
    if f.programa:
        asignaturas = asignaturas.filter(programa_id=f.programa)
    cursos = Curso.objects.all()
    if f.programa:
        cursos = cursos.filter(asignaturas_oficiales__programa_id=f.programa).distinct()
    return {
        'programas': ProgramaAcademico.objects.filter(activo=True).count(),
        'estudiantes': usuarios.get('Estudiante', 0), 'docentes': usuarios.get('Docente', 0),
        'coordinadores': usuarios.get('Coordinador', 0),
        'asignaturas': asignaturas.count(), 'cursos': cursos.count(),
        'cursos_vinculados': asignaturas.filter(curso_vinculado__isnull=False).count(),
    }


def _estado_evaluaciones(f: Filtros) -> dict:
    ahora = timezone.now()
    con_resultados = Exists(IntentoEvaluacion.objects.filter(
        evaluacion=OuterRef('pk'), enviado_en__isnull=False,
    ).exclude(integridad=OpcionesIntegridad.ANULADO_FRAUDE))
    con_entregas = Exists(EntregaTarea.objects.filter(tarea__evaluaciones_formales=OuterRef('pk'), nota__isnull=False))
    qs = _evaluaciones_base(f).annotate(con_resultados=con_resultados, con_entregas=con_entregas)
    datos = qs.aggregate(
        borradores=Count('id', filter=Q(estado=OpcionesEstadoEvaluacion.BORRADOR), distinct=True),
        publicadas=Count('id', filter=Q(estado=OpcionesEstadoEvaluacion.PUBLICADA), distinct=True),
        abiertas=Count('id', filter=Q(estado=OpcionesEstadoEvaluacion.PUBLICADA, fecha_inicio__lte=ahora,
                                     fecha_fin__gte=ahora), distinct=True),
        presentadas=Count('id', filter=Q(estado=OpcionesEstadoEvaluacion.PUBLICADA)
                          & (Q(con_resultados=True) | Q(con_entregas=True)), distinct=True),
    )
    datos['pendientes'] = datos['publicadas'] - datos['presentadas']
    return datos


def _participacion(f: Filtros) -> dict:
    """Convocatoria, asistencia y participación, en bloque (sin consultas por evaluación)."""
    evaluaciones = list(_evaluaciones_base(f).filter(estado=OpcionesEstadoEvaluacion.PUBLICADA)
                        .values('id', 'supervisor_id', 'tipo', 'tarea__asignatura__curso_vinculado_id'))
    ids = [e['id'] for e in evaluaciones]
    cursos_por_eval = defaultdict(set)
    for e in evaluaciones:
        if e['tarea__asignatura__curso_vinculado_id']:
            cursos_por_eval[e['id']].add(e['tarea__asignatura__curso_vinculado_id'])
    for ev_id, curso_id in EvaluacionPregunta.objects.filter(
        evaluacion_id__in=ids, pregunta__asignatura__curso_vinculado__isnull=False,
    ).values_list('evaluacion_id', 'pregunta__asignatura__curso_vinculado_id').distinct():
        cursos_por_eval[ev_id].add(curso_id)

    from apps.examenes.models import Curso, Inscripcion

    todos_cursos = set().union(*cursos_por_eval.values()) if cursos_por_eval else set()
    inscritos = defaultdict(set)
    for curso_id, est_id in Inscripcion.objects.filter(
        curso_id__in=todos_cursos, estudiante__role__name='Estudiante',
    ).values_list('curso_id', 'estudiante_id'):
        inscritos[curso_id].add(est_id)
    extra = defaultdict(set)
    for ev_id, est_id in ConvocadoEvaluacion.objects.filter(evaluacion_id__in=ids).values_list(
            'evaluacion_id', 'estudiante_id'):
        extra[ev_id].add(est_id)
    intentos = defaultdict(dict)
    for ev_id, est_id, enviado, integridad in IntentoEvaluacion.objects.filter(evaluacion_id__in=ids).values_list(
            'evaluacion_id', 'estudiante_id', 'enviado_en', 'integridad'):
        intentos[ev_id][est_id] = (enviado is not None, integridad)
    entregas = defaultdict(set)
    for ev_id, est_id in EntregaTarea.objects.filter(tarea__evaluaciones_formales__in=ids).values_list(
            'tarea__evaluaciones_formales', 'estudiante_id'):
        entregas[ev_id].add(est_id)
    presentes = defaultdict(set)
    for ev_id, est_id in AsistenciaEvaluacion.objects.filter(
        evaluacion_id__in=ids, estado__in=ESTADOS_PRESENTE,
    ).values_list('evaluacion_id', 'estudiante_id'):
        presentes[ev_id].add(est_id)

    total = defaultdict(int)
    por_curso = defaultdict(lambda: {'convocados': 0, 'presentaron': 0})
    for e in evaluaciones:
        ev_id = e['id']
        convocados = set().union(*(inscritos[c] for c in cursos_por_eval[ev_id])) | extra[ev_id]
        presentaron = {est for est, (enviado, integ) in intentos[ev_id].items() if enviado} | entregas[ev_id]
        total['convocados'] += len(convocados)
        total['iniciaron'] += len(intentos[ev_id]) + len(entregas[ev_id])
        total['presentaron'] += len(presentaron)
        total['anulados'] += sum(1 for _e, integ in intentos[ev_id].values() if integ == OpcionesIntegridad.ANULADO_FRAUDE)
        if e['supervisor_id']:
            total['con_control_asistencia'] += 1
            total['convocados_con_control'] += len(convocados)
            total['presentes'] += len(presentes[ev_id])
        for c in cursos_por_eval[ev_id]:
            por_curso[c]['convocados'] += len(inscritos[c])
            por_curso[c]['presentaron'] += len(inscritos[c] & presentaron)
    nombres = {c.id: (c.nombre, c.codigo) for c in Curso.objects.filter(id__in=por_curso)}
    cursos = sorted(
        ({'curso': c, 'nombre': nombres.get(c, ('Curso', ''))[0], 'codigo': nombres.get(c, ('', ''))[1], **v,
          'porcentaje': porcentaje(v['presentaron'], v['convocados'])} for c, v in por_curso.items()),
        key=lambda x: (x['porcentaje'] if x['porcentaje'] is not None else 101),
    )
    for clave in ('convocados', 'iniciaron', 'presentaron', 'anulados', 'con_control_asistencia',
                  'convocados_con_control', 'presentes'):
        total.setdefault(clave, 0)
    resumen = dict(total)
    resumen['evaluaciones'] = len(evaluaciones)
    resumen['porcentaje_participacion'] = porcentaje(resumen['presentaron'], resumen['convocados'])
    resumen['porcentaje_asistencia'] = porcentaje(resumen['presentes'], resumen['convocados_con_control'])
    return {'resumen': resumen, 'por_curso': cursos}


def _cobertura(f: Filtros) -> list:
    momentos = MomentoEvaluacion.objects.filter(activo=True).select_related('programa')
    if f.programa:
        momentos = momentos.filter(programa_id=f.programa)
    if f.momento:
        momentos = momentos.filter(id=f.momento)
    if f.semestre:
        momentos = momentos.filter(semestre_referencia=f.semestre)
    momentos = list(momentos)
    ids = [m.id for m in momentos]
    vinculos = MomentoResultado.objects.filter(momento_id__in=ids, activo=True, obligatorio=True).select_related(
        'resultado__competencia', 'resultado__asignatura')
    obligatorios = defaultdict(dict)
    for v in vinculos:
        r = v.resultado
        if f.resultado and r.id != f.resultado:
            continue
        if f.competencia and r.competencia_id != f.competencia:
            continue
        if f.asignatura and r.asignatura_id != f.asignatura:
            continue
        obligatorios[v.momento_id][r.id] = r
    evaluados = defaultdict(set)
    publicadas = EvaluacionFormal.objects.filter(momento_id__in=ids, estado=OpcionesEstadoEvaluacion.PUBLICADA)
    for m_id, r_id in EvaluacionPregunta.objects.filter(evaluacion__in=publicadas).values_list(
            'evaluacion__momento_id', 'pregunta__resultado_id').distinct():
        evaluados[m_id].add(r_id)
    for m_id, r_id in publicadas.filter(tarea__isnull=False).values_list('momento_id', 'tarea__resultado_id'):
        if r_id:
            evaluados[m_id].add(r_id)
    filas = []
    for m in momentos:
        obl = obligatorios[m.id]
        sin = [r for r_id, r in obl.items() if r_id not in evaluados[m.id]]
        filas.append({
            'momento': m.id, 'nombre': m.nombre, 'programa': m.programa.codigo, 'programa_id': m.programa_id,
            'semestre': m.semestre_referencia, 'obligatorios': len(obl), 'evaluados': len(obl) - len(sin),
            'porcentaje': porcentaje(len(obl) - len(sin), len(obl)),
            'sin_evaluar': [{'id': r.id, 'descripcion': r.descripcion, 'competencia': r.competencia.nombre}
                            for r in sin],
        })
    return filas


def _alertas(f: Filtros) -> dict:
    qs = AlertaDesempeno.objects.filter(estado=OpcionesEstadoAlerta.ABIERTA)
    if f.programa:
        qs = qs.filter(programa_id=f.programa)
    if f.asignatura:
        qs = qs.filter(asignatura_id=f.asignatura)
    por_tipo = dict(qs.values_list('tipo').annotate(n=Count('id')))
    return {'abiertas': sum(por_tipo.values()), 'por_tipo': por_tipo}


def _integridad(f: Filtros) -> dict:
    evaluaciones = _evaluaciones_base(f)
    incidentes = IncidenteIntento.objects.filter(consecuencia=OpcionesConsecuencia.SUSPENSION,
                                                 intento__evaluacion__in=evaluaciones)
    intentos = IntentoEvaluacion.objects.filter(evaluacion__in=evaluaciones)
    return {
        'suspensiones': incidentes.count(),
        'anulaciones': intentos.filter(integridad=OpcionesIntegridad.ANULADO_FRAUDE).count(),
        'reactivaciones': ResolucionIntegridad.objects.filter(
            accion=OpcionesAccionIntegridad.REACTIVAR, intento__evaluacion__in=evaluaciones).count(),
        'suspendidos_ahora': intentos.filter(integridad=OpcionesIntegridad.SUSPENDIDO).count(),
    }


# ---------------------------------------------------------------- mapas de calor

def _mapa(obs, clave_fila, etiqueta_fila, clave_col, etiqueta_col, filtro_celda, orden_col=None):
    filas, columnas = {}, {}
    grupos = _acumular(obs, lambda o: (clave_fila(o), clave_col(o)))
    for o in obs:
        filas.setdefault(clave_fila(o), etiqueta_fila(o))
        columnas.setdefault(clave_col(o), etiqueta_col(o))
    cols = sorted(columnas.items(), key=orden_col or (lambda kv: str(kv[1]['nombre'])))
    return {
        'filas': [{'id': k, **v} for k, v in sorted(filas.items(), key=lambda kv: str(kv[1]['nombre']))],
        'columnas': [{'id': k, **v} for k, v in cols],
        'celdas': [{'fila': fi, 'columna': co, **_medida(g), 'filtro': filtro_celda(fi, co)}
                   for (fi, co), g in grupos.items()],
    }


def _mapas(obs, participacion) -> dict:
    def ra(o):
        return {'nombre': o.resultado.descripcion, 'competencia': o.competencia.nombre}

    def asig(o):
        return {'nombre': f'{o.asignatura.codigo} · {o.asignatura.nombre}', 'codigo': o.asignatura.codigo}

    errores = _acumular(obs, lambda o: o.pregunta.id)
    por_pregunta = {o.pregunta.id: o for o in obs}
    preguntas = sorted(
        ({'pregunta': pid, 'enunciado': por_pregunta[pid].pregunta.enunciado[:160],
          'asignatura': por_pregunta[pid].asignatura.codigo, 'resultado': por_pregunta[pid].resultado.descripcion,
          'presentadas': g['presentadas'], 'errores': g['presentadas'] - g['aciertos'],
          'porcentaje_error': porcentaje(g['presentadas'] - g['aciertos'], g['presentadas']),
          'filtro': {'resultado': por_pregunta[pid].resultado.id, 'asignatura': por_pregunta[pid].asignatura.id}}
         for pid, g in errores.items()),
        key=lambda x: (-(x['porcentaje_error'] or 0), -x['presentadas']),
    )[:TOP_PREGUNTAS_ERROR]
    return {
        'ra_asignatura': _mapa(obs, lambda o: o.resultado.id, ra, lambda o: o.asignatura.id, asig,
                               lambda fi, co: {'resultado': fi, 'asignatura': co}),
        'competencia_programa': _mapa(
            obs, lambda o: o.competencia.id, lambda o: {'nombre': o.competencia.nombre, 'tipo': o.competencia.tipo},
            lambda o: o.programa.id, lambda o: {'nombre': o.programa.codigo, 'detalle': o.programa.nombre},
            lambda fi, co: {'competencia': fi, 'programa': co}),
        'ra_momento': _mapa(
            obs, lambda o: o.resultado.id, ra, lambda o: o.momento.id,
            lambda o: {'nombre': o.momento.nombre, 'detalle': o.programa.codigo, 'orden': o.evaluacion.fecha_inicio},
            lambda fi, co: {'resultado': fi, 'momento': co},
            orden_col=lambda kv: kv[1]['orden']),
        'preguntas_error': preguntas,
        'participacion_curso': participacion['por_curso'],
    }


def _tendencia(obs) -> dict:
    """Evolución entre momentos: solo con 2 o más momentos con datos."""
    orden = {}
    for o in obs:
        actual = orden.get(o.momento.id)
        if actual is None or o.evaluacion.fecha_inicio < actual[0]:
            orden[o.momento.id] = (o.evaluacion.fecha_inicio, o.momento.nombre, o.programa.codigo)
    if len(orden) < 2:
        return {'disponible': False, 'momentos': [],
                'motivo': 'Se necesitan resultados en al menos dos momentos de evaluación para mostrar una tendencia.'}
    momentos = sorted(orden.items(), key=lambda kv: kv[1][0])
    general = _acumular(obs, lambda o: o.momento.id)
    por_ra = _acumular(obs, lambda o: (o.resultado.id, o.momento.id))
    volumen = defaultdict(int)
    nombres = {}
    for o in obs:
        volumen[o.resultado.id] += 1
        nombres[o.resultado.id] = o.resultado.descripcion
    principales = sorted(volumen, key=lambda r: -volumen[r])[:MAX_SERIES_TENDENCIA]
    return {
        'disponible': True,
        'momentos': [{'id': m_id, 'nombre': nombre, 'programa': codigo} for m_id, (_f, nombre, codigo) in momentos],
        'general': [{'momento': m_id, **_medida(general[m_id])} for m_id, _ in momentos],
        'series': [
            {'resultado': r, 'nombre': nombres[r], 'puntos': [
                {'momento': m_id, **(_medida(por_ra[(r, m_id)]) if (r, m_id) in por_ra else
                                     {'porcentaje': None, 'presentadas': 0, 'estudiantes': 0})}
                for m_id, _ in momentos]}
            for r in principales
        ],
    }


# --------------------------------------------------------------- nivel y ruta

NIVELES_RUTA = [
    ('evaluacion', 'Evaluación'), ('resultado', 'Resultado de aprendizaje'), ('asignatura', 'Asignatura'),
    ('semestre', 'Semestre'), ('programa', 'Programa'),
]


def _nivel(f: Filtros) -> str:
    for clave, _ in NIVELES_RUTA:
        if getattr(f, clave):
            return clave
    return 'institucion'


def _ruta(f: Filtros) -> list:
    """Migas del drill-down: institución → programa → semestre → asignatura → RA → evaluación."""
    ruta = [{'nivel': 'institucion', 'nombre': 'Institución', 'filtros': {}}]
    acumulado = {}
    modelos = {
        'programa': (ProgramaAcademico, lambda o: f'{o.codigo} · {o.nombre}'),
        'asignatura': (AsignaturaMalla, lambda o: f'{o.codigo} · {o.nombre}'),
        'resultado': (ResultadoAprendizaje, lambda o: o.descripcion),
        'evaluacion': (EvaluacionFormal, lambda o: o.nombre),
    }
    for clave in ('programa', 'semestre', 'asignatura', 'resultado', 'evaluacion'):
        valor = getattr(f, clave)
        if not valor:
            continue
        acumulado[clave] = valor
        if clave == 'semestre':
            nombre = f'Semestre {valor}'
        else:
            modelo, etiqueta = modelos[clave]
            objeto = modelo.objects.filter(pk=valor).first()
            nombre = etiqueta(objeto) if objeto else f'{clave} {valor}'
        ruta.append({'nivel': clave, 'nombre': nombre, 'filtros': dict(acumulado)})
    return ruta


def _desglose(f: Filtros, obs) -> dict:
    nivel = _nivel(f)
    siguiente = {
        'institucion': ('programa', 'Programa', lambda o: o.programa.id, lambda o: f'{o.programa.codigo} · {o.programa.nombre}'),
        'programa': ('semestre', 'Semestre', lambda o: o.semestre or 0,
                     lambda o: f'Semestre {o.semestre}' if o.semestre else 'Sin semestre en la malla'),
        'semestre': ('asignatura', 'Asignatura', lambda o: o.asignatura.id,
                     lambda o: f'{o.asignatura.codigo} · {o.asignatura.nombre}'),
        'asignatura': ('resultado', 'Resultado de aprendizaje', lambda o: o.resultado.id,
                       lambda o: o.resultado.descripcion),
        'resultado': ('evaluacion', 'Evaluación', lambda o: o.evaluacion.id,
                      lambda o: f'{o.evaluacion.nombre} ({o.momento.nombre})'),
        'evaluacion': (None, 'Pregunta', lambda o: o.pregunta.id, lambda o: o.pregunta.enunciado[:120]),
    }[nivel]
    clave_filtro, titulo, clave, etiqueta = siguiente
    grupos = _acumular(obs, clave)
    nombres = {}
    for o in obs:
        nombres.setdefault(clave(o), etiqueta(o))
    filas = sorted(
        ({'id': k, 'nombre': nombres[k], **_medida(g),
          'filtro': ({clave_filtro: k} if clave_filtro and k else None)} for k, g in grupos.items()),
        key=lambda x: x['nombre'],
    )
    return {'nivel': clave_filtro, 'titulo': titulo, 'filas': filas}


# ---------------------------------------------------------------------- reporte

def analitica(f: Filtros, obs=None) -> dict:
    obs = observaciones(f) if obs is None else obs
    participacion = _participacion(f)
    por_ra = _acumular(obs, lambda o: o.resultado.id)
    por_comp = _acumular(obs, lambda o: o.competencia.id)
    por_tipo = _acumular(obs, lambda o: o.competencia.tipo)
    info_ra, info_comp = {}, {}
    for o in obs:
        info_ra.setdefault(o.resultado.id, {
            'descripcion': o.resultado.descripcion, 'competencia': o.competencia.nombre,
            'tipo': o.competencia.tipo, 'asignatura': o.asignatura.codigo, 'programa': o.programa.codigo})
        info_comp.setdefault(o.competencia.id, {'nombre': o.competencia.nombre, 'tipo': o.competencia.tipo,
                                                'programa': o.programa.codigo})
    logro_ra = sorted(
        ({'id': r, **info_ra[r], **_medida(g), 'filtro': {'resultado': r}} for r, g in por_ra.items()),
        key=lambda x: (x['porcentaje'] if x['porcentaje'] is not None else 101),
    )
    logro_comp = sorted(
        ({'id': c, **info_comp[c], **_medida(g), 'filtro': {'competencia': c}} for c, g in por_comp.items()),
        key=lambda x: (x['porcentaje'] if x['porcentaje'] is not None else 101),
    )
    total = _acumular(obs, lambda o: 'total')['total'] if obs else {'aciertos': 0, 'presentadas': 0, 'estudiantes': set()}
    filas_notas = notas(f, obs)
    datos = {
        'filtros': f.aplicados(),
        'nivel': _nivel(f),
        'ruta': _ruta(f),
        'fecha_corte': timezone.localtime(timezone=ZONA_INSTITUCIONAL),
        'metrica_provisional': {
            'aviso': 'Métrica provisional: pendiente de definición con Vicerrectoría (ADR-006).',
            'umbral_logro_porcentaje': METRICA_PROVISIONAL['umbral_logro_porcentaje'],
            'sin_responder_es_fallo': METRICA_PROVISIONAL['sin_responder_es_fallo'],
        },
        'contexto': _contexto(f),
        'logro_general': {**_medida(total), 'ra_evaluados': len(por_ra),
                          'ra_logrados': sum(1 for g in por_ra.values() if ra_logrado(porcentaje(g['aciertos'], g['presentadas'])))},
        'logro_ra': logro_ra,
        'logro_competencia': logro_comp,
        'logro_por_tipo': {t: _medida(g) for t, g in por_tipo.items()},
        'cobertura': _cobertura(f),
        'evaluaciones': _estado_evaluaciones(f),
        'participacion': participacion['resumen'],
        'niveles': niveles(filas_notas),
        'alertas': _alertas(f),
        'integridad': _integridad(f),
        'mapas': _mapas(obs, participacion),
        'tendencia': _tendencia(obs),
        'desglose': _desglose(f, obs),
    }
    # Capa interpretativa (ADR-015): comparación, calidad de datos, hallazgos y conclusiones.
    from .servicio_hallazgos import calidad_datos, comparacion, conclusiones, hallazgos
    from .servicio_indicadores import NO_DISPONIBLES

    datos['comparacion'] = comparacion(obs, datos)
    datos['calidad_datos'] = calidad_datos(f.programa)
    datos['hallazgos'] = hallazgos(datos)
    datos['conclusiones'] = conclusiones(datos)
    datos['indicadores_no_disponibles'] = NO_DISPONIBLES
    return datos


def opciones(programa_id=None, semestre=None) -> dict:
    """Valores para los selectores de filtros (dependen del programa y el semestre elegidos)."""
    from apps.users.models import User

    asignaturas = AsignaturaMalla.objects.filter(activo=True).select_related('semestre')
    momentos = MomentoEvaluacion.objects.filter(activo=True)
    competencias = Competencia.objects.filter(activo=True)
    if programa_id:
        asignaturas = asignaturas.filter(programa_id=programa_id)
        momentos = momentos.filter(programa_id=programa_id)
        competencias = competencias.filter(programa_id=programa_id)
    semestres = sorted({a.semestre.numero for a in asignaturas if a.semestre_id})
    if semestre:
        asignaturas = asignaturas.filter(semestre__numero=semestre)
    docentes = User.objects.filter(
        role__name='Docente', cursos__asignaturas_oficiales__in=asignaturas,
    ).distinct().order_by('first_name', 'first_last_name')
    return {
        'programas': [{'id': p.id, 'nombre': f'{p.codigo} · {p.nombre}'}
                      for p in ProgramaAcademico.objects.filter(activo=True).order_by('codigo')],
        'semestres': [{'id': n, 'nombre': f'Semestre {n}'} for n in semestres],
        'momentos': [{'id': m.id, 'nombre': f'{m.nombre} · {m.programa.codigo}'}
                     for m in momentos.select_related('programa').order_by('programa__codigo', 'semestre_referencia')],
        'asignaturas': [{'id': a.id, 'nombre': f'{a.codigo} · {a.nombre}'} for a in asignaturas.order_by('codigo')],
        'docentes': [{'id': d.id, 'nombre': f'{d.first_name} {d.first_last_name}'.strip() or d.email} for d in docentes],
        'competencias': [{'id': c.id, 'nombre': f'{c.nombre} ({c.get_tipo_display()})'}
                         for c in competencias.order_by('nombre')],
    }
