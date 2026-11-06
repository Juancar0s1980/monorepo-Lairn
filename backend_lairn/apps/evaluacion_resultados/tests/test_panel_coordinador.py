"""
Pruebas del panel de inicio del Coordinador (ADR-013).
Reutiliza el escenario de la analítica de RA (programa P1, momentos M1/M2,
evaluaciones E1/E2, curso C1 del docente D con 3 inscritos).
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    IntentoEvaluacion,
    PreguntaBanco,
    ProgramaAcademico,
)
from apps.evaluacion_resultados.tests.test_analitica_ra import BaseAnalitica, _usuario

URL = '/api/evaluacion/panel-coordinador/'


class PruebasPanelCoordinador(BaseAnalitica):
    def setUp(self):
        super().setUp()
        self.coordinador = _usuario('coord@t.co', 'Coordinador')
        self.cliente.force_authenticate(self.coordinador)
        PreguntaBanco.objects.create(asignatura=self.a2, resultado=self.ra2, enunciado='Pendiente', opciones=['a', 'b'],
                                     respuesta_correcta=0, estado='pendiente')
        AlertaDesempeno.objects.create(tipo='estudiante', programa=self.programa, estudiante=self.est[1],
                                       actividades_bajas=3, total_actividades=4)
        IntentoEvaluacion.objects.create(evaluacion=self.e2, estudiante=self.est[2], vence_en=self.ahora,
                                         integridad='suspendido')

    def datos(self, **params):
        r = self.cliente.get(URL, params)
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        return r.data

    def test_cobertura_y_evaluaciones_por_momento(self):
        d = self.datos(programa=self.programa.id)
        m1 = next(m for m in d['momentos'] if m['nombre'] == 'M1')
        self.assertEqual((m1['obligatorios'], m1['evaluados'], m1['publicadas']), (3, 2, 1))
        self.assertEqual([r['descripcion'] for r in m1['sin_evaluar']], ['RA3'])
        self.assertEqual(d['evaluaciones']['publicadas'], 2)

    def test_banco_docentes_alertas_e_integridad(self):
        d = self.datos(programa=self.programa.id)
        self.assertEqual(d['banco']['pendientes'], 1)
        a2 = next(f for f in d['banco']['por_asignatura'] if f['codigo'] == 'A2')
        self.assertEqual((a2['pendientes'], a2['aprobadas']), (1, 1))
        self.assertEqual([x['email'] for x in d['docentes']['docentes']], ['doc@t.co'])
        self.assertEqual(d['docentes']['docentes'][0]['asignaturas'], ['A1'])
        self.assertEqual((d['docentes']['asignaturas_con_curso'], d['docentes']['asignaturas_sin_curso']), (1, 1))
        self.assertEqual(d['alertas']['abiertas'], 1)
        self.assertEqual(d['alertas']['recientes'][0]['actividades_bajas'], 3)
        suspendidos = d['integridad']['suspendidos']
        self.assertEqual((len(suspendidos), suspendidos[0]['decide']), (1, 'Coordinador o Administrador'))
        self.assertEqual(d['participacion']['convocados'], 6)

    def test_filtro_por_programa(self):
        otro = ProgramaAcademico.objects.create(codigo='P9', nombre='Otro')
        d = self.datos(programa=otro.id)
        self.assertEqual((d['momentos'], d['banco']['pendientes'], d['alertas']['abiertas']), ([], 0, 0))
        self.assertEqual(d['integridad']['suspendidos'], [])
        self.assertEqual(self.cliente.get(URL, {'programa': 'x'}).status_code, 400)
        self.assertEqual({p['nombre'] for p in self.datos()['programas']}, {'P1 · Ingeniería', 'P9 · Otro'})

    def test_permisos(self):
        self.cliente.force_authenticate(_usuario('adm@t.co', 'Administrador'))
        self.assertEqual(self.cliente.get(URL).status_code, 200)
        for rol in ('Vicerrector', 'Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@x.co', rol))
                self.assertEqual(self.cliente.get(URL).status_code, 403)
        # El panel no abre lo que es solo del Administrador.
        self.cliente.force_authenticate(self.coordinador)
        self.assertEqual(self.cliente.get(f'/api/evaluacion/programas/{self.programa.id}/desempeno-ra/').status_code, 403)

    def test_sin_consultas_n_mas_uno(self):
        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                self.cliente.get(URL, {'programa': self.programa.id})
            return len(capturadas)

        antes = consultas()
        for i in range(5):
            e = _usuario(f'mas{i}@t.co', 'Estudiante')
            self._intento(self.e1, e, {self.q1: 0, self.q2: 0})
            PreguntaBanco.objects.create(asignatura=self.a1, resultado=self.ra1, enunciado=f'X{i}', opciones=['a', 'b'],
                                         respuesta_correcta=0, estado='pendiente')
        self.assertEqual(consultas(), antes)
        self.assertEqual(IntentoEvaluacion.objects.filter(integridad='suspendido').count(), 1)
