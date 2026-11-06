"""
Listado consultable de estudiantes convocados e inscritos (ADR-012).

Conceptos (no confundir):
  - Inscripción  = estudiante en un `examenes.Curso` (con código).
  - Convocatoria = llamado a una evaluación formal: inscrito en un curso
    vinculado a sus asignaturas (origen "curso") o agregado por cargue ("cargue").
  - Asistencia   = llamado a lista del supervisor (presente/tarde).
  - Participación = intento enviado o entrega real ("presentó").
  - Registro (cuenta) lo crea TI: aquí nunca se crean cuentas.

Alcance por rol:
  - Administrador / Coordinador: cursos vinculados a la malla (del programa
    filtrado) y evaluaciones del programa/momento/evaluación filtrados.
  - Docente: solo los estudiantes de SUS cursos y de las evaluaciones que SUPERVISA.
  - Vicerrector: no ve el listado nominal (solo consolidados en el reporte).

Todo se calcula en bloque (número fijo de consultas) y se pagina en el servidor.
"""

import csv
import io
from collections import defaultdict
from dataclasses import dataclass, field

from apps.evaluacion_resultados.models import (
    AsistenciaEvaluacion,
    ConvocadoEvaluacion,
    EntregaTarea,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    OpcionesEstadoEvaluacion,
    OpcionesIntegridad,
)

from .servicio_supervision import _normalizar, nombre_completo

ESTADOS = {
    'inscrito': 'Inscrito en un curso',
    'convocado_curso': 'Convocado por curso',
    'convocado_cargue': 'Convocado por cargue',
    'presente': 'Presente en sala',
    'presento': 'Presentó',
    'no_presento': 'Convocado que no ha presentado',
    'suspendido': 'Suspendido',
    'anulado': 'Anulado por fraude',
}
TAMANO_PAGINA, MAX_TAMANO_PAGINA = 25, 100


@dataclass
class Alcance:
    cursos: object               # QuerySet de examenes.Curso
    evaluaciones: object         # QuerySet de EvaluacionFormal
    detalle_evaluacion: object = None  # EvaluacionFormal si se filtró por una sola


def alcance_gestor(programa=None, momento=None, evaluacion=None) -> Alcance:
    from apps.examenes.models import Curso

    cursos = Curso.objects.filter(asignaturas_oficiales__isnull=False)
    evaluaciones = EvaluacionFormal.objects.filter(estado=OpcionesEstadoEvaluacion.PUBLICADA)
    if programa:
        cursos = cursos.filter(asignaturas_oficiales__programa_id=programa)
        evaluaciones = evaluaciones.filter(momento__programa_id=programa)
    if momento:
        evaluaciones = evaluaciones.filter(momento_id=momento)
    detalle = None
    if evaluacion:
        evaluaciones = evaluaciones.filter(id=evaluacion)
        detalle = evaluaciones.first()
    return Alcance(cursos=cursos.distinct(), evaluaciones=evaluaciones, detalle_evaluacion=detalle)


def alcance_docente(docente, evaluacion=None) -> Alcance:
    from apps.examenes.models import Curso

    evaluaciones = EvaluacionFormal.objects.filter(supervisor=docente, estado=OpcionesEstadoEvaluacion.PUBLICADA)
    detalle = None
    if evaluacion:
        evaluaciones = evaluaciones.filter(id=evaluacion)
        detalle = evaluaciones.first()
    return Alcance(cursos=Curso.objects.filter(docente=docente), evaluaciones=evaluaciones, detalle_evaluacion=detalle)


@dataclass
class _Fila:
    estudiante: int
    cursos: set = field(default_factory=set)
    convocatorias: dict = field(default_factory=dict)   # evaluacion_id -> 'curso' | 'cargue'
    presente: set = field(default_factory=set)
    presento: set = field(default_factory=set)
    suspendido: set = field(default_factory=set)
    anulado: set = field(default_factory=set)
    intento: dict = field(default_factory=dict)         # evaluacion_id -> (estado, integridad)


def _calcular(alcance: Alcance) -> dict:
    from apps.examenes.models import Inscripcion

    filas = defaultdict(lambda: None)

    def fila(est_id):
        if filas[est_id] is None:
            filas[est_id] = _Fila(estudiante=est_id)
        return filas[est_id]

    cursos = {c.id: c for c in alcance.cursos}
    evaluaciones = list(alcance.evaluaciones.values('id', 'nombre', 'momento__nombre',
                                                    'tarea__asignatura__curso_vinculado_id'))
    ids = [e['id'] for e in evaluaciones]

    # Inscripciones en los cursos del alcance.
    inscritos_por_curso = defaultdict(set)
    for curso_id, est_id in Inscripcion.objects.filter(
        curso_id__in=cursos, estudiante__role__name='Estudiante',
    ).values_list('curso_id', 'estudiante_id'):
        inscritos_por_curso[curso_id].add(est_id)
        fila(est_id).cursos.add(curso_id)

    # Convocatoria por curso: inscritos en los cursos vinculados a las asignaturas de cada evaluación.
    cursos_por_eval = defaultdict(set)
    for e in evaluaciones:
        if e['tarea__asignatura__curso_vinculado_id']:
            cursos_por_eval[e['id']].add(e['tarea__asignatura__curso_vinculado_id'])
    for ev_id, curso_id in EvaluacionPregunta.objects.filter(
        evaluacion_id__in=ids, pregunta__asignatura__curso_vinculado__isnull=False,
    ).values_list('evaluacion_id', 'pregunta__asignatura__curso_vinculado_id').distinct():
        cursos_por_eval[ev_id].add(curso_id)
    faltantes = set().union(*cursos_por_eval.values()) - set(inscritos_por_curso) if cursos_por_eval else set()
    for curso_id, est_id in Inscripcion.objects.filter(
        curso_id__in=faltantes, estudiante__role__name='Estudiante',
    ).values_list('curso_id', 'estudiante_id'):
        inscritos_por_curso[curso_id].add(est_id)
    for ev_id, cursos_ev in cursos_por_eval.items():
        for curso_id in cursos_ev:
            for est_id in inscritos_por_curso[curso_id]:
                fila(est_id).convocatorias[ev_id] = 'curso'
    for ev_id, est_id in ConvocadoEvaluacion.objects.filter(evaluacion_id__in=ids).values_list(
            'evaluacion_id', 'estudiante_id'):
        fila(est_id).convocatorias.setdefault(ev_id, 'cargue')

    for ev_id, est_id in AsistenciaEvaluacion.objects.filter(
        evaluacion_id__in=ids, estado__in=('presente', 'tarde'),
    ).values_list('evaluacion_id', 'estudiante_id'):
        fila(est_id).presente.add(ev_id)
    for ev_id, est_id, enviado, integridad in IntentoEvaluacion.objects.filter(evaluacion_id__in=ids).values_list(
            'evaluacion_id', 'estudiante_id', 'enviado_en', 'integridad'):
        f = fila(est_id)
        f.intento[ev_id] = ('enviado' if enviado else 'en_curso', integridad)
        if integridad == OpcionesIntegridad.ANULADO_FRAUDE:
            f.anulado.add(ev_id)
        elif enviado:
            f.presento.add(ev_id)
        if integridad == OpcionesIntegridad.SUSPENDIDO:
            f.suspendido.add(ev_id)
    for ev_id, est_id in EntregaTarea.objects.filter(tarea__evaluaciones_formales__in=ids).values_list(
            'tarea__evaluaciones_formales', 'estudiante_id'):
        fila(est_id).presento.add(ev_id)
    return {'filas': {k: v for k, v in filas.items() if v is not None}, 'cursos': cursos, 'evaluaciones': evaluaciones}


def _estados_de(f: _Fila) -> set:
    estados = set()
    if f.cursos:
        estados.add('inscrito')
    origenes = set(f.convocatorias.values())
    if 'curso' in origenes:
        estados.add('convocado_curso')
    if 'cargue' in origenes:
        estados.add('convocado_cargue')
    if f.presente:
        estados.add('presente')
    if f.presento:
        estados.add('presento')
    if set(f.convocatorias) - f.presento - f.anulado:
        estados.add('no_presento')
    if f.suspendido:
        estados.add('suspendido')
    if f.anulado:
        estados.add('anulado')
    return estados


def listado(alcance: Alcance, *, estado=None, buscar='', pagina=1, tamano=TAMANO_PAGINA, paginar=True) -> dict:
    from apps.users.models import User

    calculo = _calcular(alcance)
    usuarios = {u.id: u for u in User.objects.filter(id__in=calculo['filas']).select_related(
        'perfil_academico__programa')}
    detalle = alcance.detalle_evaluacion
    termino = _normalizar(buscar)
    conteos = dict.fromkeys(ESTADOS, 0)
    filas = []
    for est_id, f in calculo['filas'].items():
        u = usuarios.get(est_id)
        if u is None:
            continue
        perfil = getattr(u, 'perfil_academico', None)
        estados = _estados_de(f)
        nombre = nombre_completo(u)
        codigo = perfil.codigo_matricula if perfil else ''
        if termino and termino not in _normalizar(f'{nombre} {u.email} {codigo}'):
            continue
        for e in estados:
            conteos[e] += 1
        if estado and estado not in estados:
            continue
        registro = {
            'estudiante': est_id, 'nombre': nombre, 'email': u.email, 'codigo': codigo or None,
            'programa': perfil.programa.codigo if perfil and perfil.programa_id else None,
            'semestre': perfil.semestre_actual if perfil else None,
            'cursos': sorted(calculo['cursos'][c].nombre for c in f.cursos if c in calculo['cursos']),
            'convocatorias': len(f.convocatorias),
            'origenes': sorted(set(f.convocatorias.values())),
            'presente': len(f.presente), 'presento': len(f.presento),
            'suspendido': len(f.suspendido), 'anulado': len(f.anulado),
            'estados': sorted(estados),
        }
        if detalle is not None:
            intento = f.intento.get(detalle.id)
            registro['en_evaluacion'] = {
                'origen': f.convocatorias.get(detalle.id),
                'presente': detalle.id in f.presente,
                'intento': intento[0] if intento else None,
                'integridad': intento[1] if intento else None,
            }
        filas.append(registro)
    filas.sort(key=lambda r: _normalizar(r['nombre']))
    total = len(filas)
    tamano = max(1, min(int(tamano or TAMANO_PAGINA), MAX_TAMANO_PAGINA))
    paginas = max(1, -(-total // tamano))
    pagina = max(1, min(int(pagina or 1), paginas))
    if paginar:
        filas = filas[(pagina - 1) * tamano: pagina * tamano]
    return {
        'total': total, 'pagina': pagina, 'paginas': paginas, 'tamano': tamano,
        'conteos': conteos, 'estados': ESTADOS, 'filas': filas,
        'evaluaciones': [{'id': e['id'], 'nombre': f"{e['nombre']} · {e['momento__nombre']}"}
                         for e in calculo['evaluaciones']],
        'evaluacion': {'id': detalle.id, 'nombre': detalle.nombre} if detalle is not None else None,
    }


ENCABEZADO_EXPORTACION = ['Nombre', 'Correo', 'Código', 'Programa', 'Semestre', 'Cursos', 'Convocatorias',
                          'Origen', 'Presente', 'Presentó', 'Suspendido', 'Anulado', 'Estados']


def _fila_exportacion(r) -> list:
    return [r['nombre'], r['email'], r['codigo'] or '', r['programa'] or '', r['semestre'] or '',
            '; '.join(r['cursos']), r['convocatorias'], ', '.join(r['origenes']), r['presente'], r['presento'],
            r['suspendido'], r['anulado'], ', '.join(ESTADOS[e] for e in r['estados'])]


def exportar(datos, formato: str) -> bytes:
    if formato == 'csv':
        salida = io.StringIO()
        escritor = csv.writer(salida, delimiter=';')
        escritor.writerow(ENCABEZADO_EXPORTACION)
        for r in datos['filas']:
            escritor.writerow(_fila_exportacion(r))
        return ('﻿' + salida.getvalue()).encode('utf-8')  # BOM: Excel abre bien las tildes
    from openpyxl import Workbook
    from openpyxl.styles import Font

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Estudiantes'
    hoja.append(ENCABEZADO_EXPORTACION)
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for r in datos['filas']:
        hoja.append(_fila_exportacion(r))
    hoja.column_dimensions['A'].width = 34
    hoja.column_dimensions['B'].width = 34
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
