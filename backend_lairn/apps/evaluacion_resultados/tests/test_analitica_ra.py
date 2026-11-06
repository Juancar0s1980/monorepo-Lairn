"""
Pruebas de la analítica de RA para Vicerrectoría (ADR-011).

Escenario (programa P1):
- A1 (semestre 1, curso C1 del docente D) y A2 (semestre 2, sin curso).
- Competencias: Cesp (específica) y Ctra (transversal).
- RA1 (A1, Cesp), RA2 (A2, Ctra) y RA3 (A1, Cesp, obligatorio en M1 pero sin preguntas).
- M1 → E1 con q1 (RA1) y q2 (RA2): est1 acierta ambas; est2 acierta q1 y falla q2; est3 no presenta.
- M2 → E2 con q3 (RA1): est1 falla.
Resultados: RA1 = 2/3 = 66,7 %; RA2 = 1/2 = 50 %; tendencia RA1: M1 100 % → M2 0 %.
"""

from datetime import timedelta
from io import BytesIO

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    MomentoEvaluacion,
    MomentoResultado,
    PreguntaBanco,
    ProgramaAcademico,
    ResultadoAprendizaje,
    SemestrePrograma,
)
from apps.examenes.models import Curso, Inscripcion
from apps.users.models import Role, User

URL = '/api/evaluacion/reporte-ejecutivo/'


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name=email.split('@')[0], first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class BaseAnalitica(TestCase):
    def setUp(self):
        self.ahora = timezone.now()
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ingeniería')
        s1 = SemestrePrograma.objects.create(programa=self.programa, numero=1)
        s2 = SemestrePrograma.objects.create(programa=self.programa, numero=2)
        self.docente = _usuario('doc@t.co', 'Docente')
        self.curso = Curso.objects.create(nombre='C1', docente=self.docente)
        self.a1 = AsignaturaMalla.objects.create(codigo='A1', nombre='Uno', programa=self.programa, semestre=s1,
                                                 curso_vinculado=self.curso)
        self.a2 = AsignaturaMalla.objects.create(codigo='A2', nombre='Dos', programa=self.programa, semestre=s2)
        self.cesp = Competencia.objects.create(programa=self.programa, nombre='Cesp', tipo='especifica')
        self.ctra = Competencia.objects.create(programa=self.programa, nombre='Ctra', tipo='transversal')
        self.ra1 = ResultadoAprendizaje.objects.create(competencia=self.cesp, asignatura=self.a1, descripcion='RA1')
        self.ra2 = ResultadoAprendizaje.objects.create(competencia=self.ctra, asignatura=self.a2, descripcion='RA2')
        self.ra3 = ResultadoAprendizaje.objects.create(competencia=self.cesp, asignatura=self.a1, descripcion='RA3')
        self.m1 = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=1, nombre='M1')
        self.m2 = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=1, nombre='M2')
        for ra in (self.ra1, self.ra2, self.ra3):
            MomentoResultado.objects.create(momento=self.m1, resultado=ra, obligatorio=True)
        self.e1 = self._evaluacion(self.m1, 'E1', dias=-10)
        self.e2 = self._evaluacion(self.m2, 'E2', dias=-1)
        self.q1 = self._pregunta(self.a1, self.ra1, self.e1)
        self.q2 = self._pregunta(self.a2, self.ra2, self.e1)
        self.q3 = self._pregunta(self.a1, self.ra1, self.e2)
        self.est = [_usuario(f'est{i}@t.co', 'Estudiante') for i in (1, 2, 3)]
        for e in self.est:
            Inscripcion.objects.create(estudiante=e, curso=self.curso)
        self._intento(self.e1, self.est[0], {self.q1: 0, self.q2: 0})
        self._intento(self.e1, self.est[1], {self.q1: 0, self.q2: 1})
        self._intento(self.e2, self.est[0], {self.q3: 1})
        self.cliente = APIClient()
        self.cliente.force_authenticate(_usuario('vice@t.co', 'Vicerrector'))

    def _evaluacion(self, momento, nombre, dias):
        inicio = self.ahora + timedelta(days=dias)
        return EvaluacionFormal.objects.create(momento=momento, nombre=nombre, fecha_inicio=inicio,
                                               fecha_fin=inicio + timedelta(hours=2), duracion_minutos=30,
                                               estado='publicada')

    def _pregunta(self, asignatura, ra, evaluacion):
        p = PreguntaBanco.objects.create(asignatura=asignatura, resultado=ra, enunciado=f'P {ra.descripcion}',
                                         opciones=['a', 'b'], respuesta_correcta=0, estado='aprobada')
        EvaluacionPregunta.objects.create(evaluacion=evaluacion, pregunta=p)
        return p

    def _intento(self, evaluacion, estudiante, respuestas, **extra):
        cuando = evaluacion.fecha_inicio + timedelta(minutes=20)
        return IntentoEvaluacion.objects.create(
            evaluacion=evaluacion, estudiante=estudiante, vence_en=cuando, enviado_en=cuando,
            respuestas={str(p.id): v for p, v in respuestas.items()}, **extra,
        )

    def datos(self, **filtros):
        r = self.cliente.get(URL, filtros)
        self.assertEqual(r.status_code, 200, r.data)
        return r.data['analitica']


class PruebasLogro(BaseAnalitica):
    def test_logro_por_ra_y_competencia(self):
        a = self.datos()
        por_ra = {r['descripcion']: (r['porcentaje'], r['presentadas'], r['logrado']) for r in a['logro_ra']}
        self.assertEqual(por_ra, {'RA1': (66.7, 3, True), 'RA2': (50.0, 2, False)})
        por_comp = {c['nombre']: (c['tipo'], c['porcentaje']) for c in a['logro_competencia']}
        self.assertEqual(por_comp, {'Cesp': ('especifica', 66.7), 'Ctra': ('transversal', 50.0)})
        self.assertEqual(a['logro_general']['ra_logrados'], 1)
        self.assertIn('provisional', a['metrica_provisional']['aviso'])

    def test_anulados_por_fraude_no_cuentan(self):
        self._intento(self.e2, self.est[1], {self.q3: 0}, integridad='anulado_fraude')
        a = self.datos()
        self.assertEqual({r['descripcion']: r['presentadas'] for r in a['logro_ra']}['RA1'], 3)
        self.assertEqual(a['participacion']['anulados'], 1)

    def test_filtros(self):
        self.assertEqual([r['descripcion'] for r in self.datos(competencia=self.ctra.id)['logro_ra']], ['RA2'])
        self.assertEqual([r['descripcion'] for r in self.datos(semestre=1)['logro_ra']], ['RA1'])
        self.assertEqual([r['descripcion'] for r in self.datos(docente=self.docente.id)['logro_ra']], ['RA1'])
        m2 = self.datos(momento=self.m2.id)['logro_ra']
        self.assertEqual([(r['descripcion'], r['porcentaje']) for r in m2], [('RA1', 0.0)])
        hoy = timezone.localdate()
        reciente = self.datos(desde=(hoy - timedelta(days=3)).isoformat(), hasta=hoy.isoformat())
        self.assertEqual(reciente['logro_general']['presentadas'], 1)  # solo E2
        r = self.cliente.get(URL, {'semestre': 'x'})
        self.assertEqual(r.status_code, 400)
        r = self.cliente.get(URL, {'desde': '2026-05-02', 'hasta': '2026-05-01'})
        self.assertEqual(r.status_code, 400)

    def test_drill_down_y_ruta(self):
        a = self.datos()
        self.assertEqual((a['nivel'], a['desglose']['titulo']), ('institucion', 'Programa'))
        a = self.datos(programa=self.programa.id)
        self.assertEqual(a['desglose']['titulo'], 'Semestre')
        self.assertEqual({f['nombre'] for f in a['desglose']['filas']}, {'Semestre 1', 'Semestre 2'})
        a = self.datos(programa=self.programa.id, semestre=1, asignatura=self.a1.id, resultado=self.ra1.id)
        self.assertEqual(a['nivel'], 'resultado')
        self.assertEqual([r['nombre'] for r in a['ruta']], ['Institución', 'P1 · Ingeniería', 'Semestre 1',
                                                             'A1 · Uno', 'RA1'])
        self.assertEqual({f['nombre'] for f in a['desglose']['filas']}, {'E1 (M1)', 'E2 (M2)'})


class PruebasSecciones(BaseAnalitica):
    def test_cobertura_ra_obligatorios(self):
        cobertura = {c['nombre']: c for c in self.datos()['cobertura']}
        self.assertEqual((cobertura['M1']['obligatorios'], cobertura['M1']['evaluados']), (3, 2))
        self.assertEqual([r['descripcion'] for r in cobertura['M1']['sin_evaluar']], ['RA3'])

    def test_evaluaciones_y_participacion(self):
        EvaluacionFormal.objects.create(momento=self.m2, nombre='Borrador', fecha_inicio=self.ahora,
                                        fecha_fin=self.ahora + timedelta(hours=1), duracion_minutos=30)
        a = self.datos()
        ev = a['evaluaciones']
        self.assertEqual((ev['publicadas'], ev['presentadas'], ev['pendientes'], ev['borradores']), (2, 2, 0, 1))
        p = a['participacion']
        # E1 y E2 convocan a los 3 inscritos en C1 (A2 no tiene curso).
        self.assertEqual((p['convocados'], p['presentaron'], p['porcentaje_participacion']), (6, 3, 50.0))
        curso = a['mapas']['participacion_curso'][0]
        self.assertEqual((curso['nombre'], curso['convocados'], curso['presentaron']), ('C1', 6, 3))

    def test_mapas_sin_celdas_vacias_y_con_muestra(self):
        mapas = self.datos()['mapas']
        ra_asig = mapas['ra_asignatura']
        # 2 RA × 2 asignaturas posibles, pero solo hay datos en 2 combinaciones: las demás no se inventan como 0.
        self.assertEqual(len(ra_asig['celdas']), 2)
        celda = next(c for c in ra_asig['celdas'] if c['fila'] == self.ra1.id)
        self.assertEqual((celda['porcentaje'], celda['presentadas'], celda['estudiantes']), (66.7, 3, 2))
        self.assertEqual(celda['filtro'], {'resultado': self.ra1.id, 'asignatura': self.a1.id})
        self.assertEqual([c['nombre'] for c in mapas['ra_momento']['columnas']], ['M1', 'M2'])
        self.assertEqual(mapas['preguntas_error'][0]['porcentaje_error'], 100.0)  # q3: 1 de 1 falló
        self.assertEqual(len(mapas['competencia_programa']['celdas']), 2)

    def test_tendencia_requiere_dos_momentos(self):
        a = self.datos()
        self.assertTrue(a['tendencia']['disponible'])
        serie = next(s for s in a['tendencia']['series'] if s['nombre'] == 'RA1')
        self.assertEqual([p['porcentaje'] for p in serie['puntos']], [100.0, 0.0])
        solo_m1 = self.datos(momento=self.m1.id)['tendencia']
        self.assertFalse(solo_m1['disponible'])
        self.assertIn('al menos dos momentos', solo_m1['motivo'])

    def test_niveles_y_notas(self):
        a = self.datos()
        # Notas por (intento, asignatura): est1 A1 5, A2 5; est2 A1 5, A2 0; est1 E2 A1 0.
        niveles = {n['clave']: n['cantidad'] for n in a['niveles']['niveles']}
        self.assertEqual((niveles['superior'], niveles['muy_insuficiente'], a['niveles']['total']), (3, 2, 5))
        self.assertEqual(a['niveles']['aprobacion'], 60.0)

    def test_exportaciones_incluyen_la_analitica(self):
        from openpyxl import load_workbook

        excel = self.cliente.get(URL + 'exportar/', {'formato': 'xlsx', 'competencia': self.ctra.id})
        self.assertEqual(excel.status_code, 200)
        libro = load_workbook(BytesIO(excel.content))
        textos = [str(c.value) for fila in libro['Analítica RA'].iter_rows() for c in fila if c.value is not None]
        self.assertIn('RA2', textos)
        self.assertNotIn('RA1', textos)  # mismas cifras que la pantalla con el filtro
        self.assertIn('Corporación Universitaria Autónoma del Cauca', str(libro['Indicadores']['A1'].value))
        pdf = self.cliente.get(URL + 'exportar/', {'formato': 'pdf', 'programa': self.programa.id})
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertEqual(self.cliente.get(URL + 'exportar/', {'formato': 'pdf', 'momento': 'x'}).status_code, 400)


class PruebasRendimientoYPermisos(BaseAnalitica):
    def _consultas(self):
        with CaptureQueriesContext(connection) as capturadas:
            self.assertEqual(self.cliente.get(URL).status_code, 200)
        return len(capturadas)

    def test_sin_consultas_n_mas_uno(self):
        antes = self._consultas()
        for i in range(4, 10):
            est = _usuario(f'extra{i}@t.co', 'Estudiante')
            Inscripcion.objects.create(estudiante=est, curso=self.curso)
            self._intento(self.e1, est, {self.q1: 0, self.q2: 1})
            self._intento(self.e2, est, {self.q3: 0})
        self.assertEqual(self._consultas(), antes)  # más datos, mismas consultas
        self.assertLess(antes, 60)

    def test_permisos(self):
        self.assertEqual(self.cliente.get(URL + 'opciones/').status_code, 200)
        # ADR-015: el Coordinador lee el reporte (solo lectura); Docente y Estudiante no.
        for rol in ('Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@x.co', rol))
                self.assertEqual(self.cliente.get(URL + 'opciones/').status_code, 403)
                self.assertEqual(self.cliente.get(URL, {'programa': self.programa.id}).status_code, 403)

    def test_opciones_dependen_del_programa(self):
        datos = self.cliente.get(URL + 'opciones/', {'programa': self.programa.id, 'semestre': 1}).data
        self.assertEqual([s['nombre'] for s in datos['semestres']], ['Semestre 1', 'Semestre 2'])
        self.assertEqual([a['nombre'] for a in datos['asignaturas']], ['A1 · Uno'])
        self.assertEqual([d['id'] for d in datos['docentes']], [self.docente.id])
