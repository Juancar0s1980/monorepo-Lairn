"""
Pruebas de los resúmenes de inicio por rol (ADR-014).
Reutiliza el escenario de la analítica (P1, A1 con curso C1 del docente D,
A2 sin curso, E1/E2 ya cerradas, est1/est2 presentaron, est3 no).
"""

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.evaluacion_resultados.models import (
    EntregaTarea,
    EvaluacionFormal,
    EvaluacionPregunta,
    RegistroSincronizacion,
    TareaPractica,
)
from apps.evaluacion_resultados.tests.test_analitica_ra import BaseAnalitica, _usuario

API = '/api/evaluacion'


class BasePaneles(BaseAnalitica):
    def setUp(self):
        super().setUp()
        # Evaluación abierta ahora, supervisada por el docente, con una pregunta de A1 (convoca a C1).
        self.abierta = EvaluacionFormal.objects.create(
            momento=self.m2, nombre='Abierta', fecha_inicio=self.ahora - timedelta(minutes=10),
            fecha_fin=self.ahora + timedelta(hours=2), duracion_minutos=30, estado='publicada', supervisor=self.docente,
        )
        EvaluacionPregunta.objects.create(evaluacion=self.abierta, pregunta=self.q1)
        self.tarea = TareaPractica.objects.create(
            asignatura=self.a1, resultado=self.ra1, titulo='Informe', descripcion='Entregar informe',
            formatos_permitidos=['pdf'], fecha_limite=self.ahora + timedelta(days=3), estado='publicada',
        )
        EntregaTarea.objects.create(
            tarea=self.tarea, estudiante=self.est[1], archivo=SimpleUploadedFile('i.pdf', b'%PDF-1.4'),
            nombre_original='i.pdf', tamano=8, nota='4.20',
        )

    def get(self, usuario, url):
        self.cliente.force_authenticate(usuario)
        return self.cliente.get(f'{API}/{url}')


class PruebasPanelAdmin(BasePaneles):
    def test_estado_de_la_plataforma(self):
        RegistroSincronizacion.objects.create(origen='api_nova_json', entidad='programas', modo='real',
                                              total_recibidos=3, creados=2, omitidos=1, errores=['x'])
        r = self.get(_usuario('adm@t.co', 'Administrador'), 'panel-admin/')
        self.assertEqual(r.status_code, 200)
        roles = {u['rol']: u['activos'] for u in r.data['usuarios']}
        self.assertEqual((roles['Estudiante'], roles['Docente'], roles['Administrador']), (3, 1, 1))
        self.assertEqual((r.data['importaciones'][0]['creados'], r.data['importaciones'][0]['errores']), (2, 1))
        self.assertEqual([e['nombre'] for e in r.data['abiertas']], ['Abierta'])
        self.assertEqual(r.data['evaluaciones']['publicadas'], 3)

    def test_solo_administrador(self):
        for rol in ('Coordinador', 'Vicerrector', 'Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.assertEqual(self.get(_usuario(f'{rol}@x.co', rol), 'panel-admin/').status_code, 403)


class PruebasPanelDocente(BasePaneles):
    def test_solo_sus_asignaturas_y_resultados_agregados(self):
        r = self.get(self.docente, 'docente/panel/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([a['codigo'] for a in r.data['asignaturas']], ['A1'])  # A2 no tiene su curso
        self.assertEqual(r.data['banco']['aprobada'], 2)  # q1 y q3 de A1
        self.assertEqual(r.data['tareas']['publicadas'], 1)
        self.assertEqual(r.data['tareas']['proximas'][0]['entregas'], 1)
        self.assertEqual([s['nombre'] for s in r.data['supervisiones']], ['Abierta'])
        res = r.data['resultados']
        self.assertEqual([(x['descripcion'], x['porcentaje']) for x in res['por_ra']], [('RA1', 66.7)])  # RA2 es de A2
        self.assertIn('provisional', res['aviso'])
        # Sin datos por estudiante: solo conteos agregados, ni correos ni filas individuales.
        for fila in res['por_ra'] + res['preguntas_error']:
            self.assertNotIn('estudiante', fila)
        self.assertNotIn('est1@t.co', str(r.data))

    def test_otro_docente_sin_datos_y_permisos(self):
        r = self.get(_usuario('otro@t.co', 'Docente'), 'docente/panel/')
        self.assertEqual((r.data['asignaturas'], r.data['resultados']['general'], r.data['supervisiones']), ([], None, []))
        self.assertEqual(self.get(self.est[0], 'docente/panel/').status_code, 403)


class PruebasPanelEstudiante(BasePaneles):
    def test_pendientes_e_historial_sin_nota_de_la_evaluacion(self):
        r = self.get(self.est[2], 'estudiante/panel/')  # est3: inscrito, no ha presentado nada
        self.assertEqual(r.status_code, 200)
        pend = r.data['pendientes']
        self.assertEqual([e['nombre'] for e in pend['evaluaciones']], ['Abierta'])
        self.assertTrue(pend['evaluaciones'][0]['requiere_asistencia'])
        self.assertEqual([t['titulo'] for t in pend['tareas']], ['Informe'])

        r = self.get(self.est[0], 'estudiante/panel/')  # est1 presentó E1 y E2
        historial = r.data['historial']['evaluaciones']
        self.assertEqual({e['nombre'] for e in historial}, {'E1', 'E2'})
        for e in historial:
            self.assertNotIn('nota', e)  # HU-07: sin nota de la evaluación formal
            self.assertNotIn('aciertos', e)

        r = self.get(self.est[1], 'estudiante/panel/')  # est2 entregó la tarea calificada
        tarea = r.data['historial']['tareas'][0]
        self.assertEqual((tarea['titulo'], str(tarea['nota']), tarea['calificada']), ('Informe', '4.20', True))
        self.assertEqual(r.data['pendientes']['tareas'], [])

    def test_permisos(self):
        self.assertEqual(self.get(self.docente, 'estudiante/panel/').status_code, 403)
