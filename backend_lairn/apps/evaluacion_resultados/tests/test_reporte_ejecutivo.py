"""
Pruebas del reporte ejecutivo (HU-11.1 a 11.3) y del rol Vicerrector.

Escenario: programa P1 con dos materias (A1, A2) y una evaluación de 2
preguntas (una por materia), presentada por 2 estudiantes:
- Ana acierta ambas  -> A1 5.0, A2 5.0
- Beto acierta solo A1 -> A1 5.0, A2 0.0
Resultados: [5, 5, 5, 0] -> promedio 3.75; 3 sobre la media, 1 bajo.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    MomentoEvaluacion,
    PreguntaBanco,
    ProgramaAcademico,
    ResultadoAprendizaje,
)
from apps.users.models import Role, User

URL = '/api/evaluacion/reporte-ejecutivo/'


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name='N', first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class PruebasReporteEjecutivo(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ingeniería')
        ProgramaAcademico.objects.create(codigo='P2', nombre='Sin datos')
        comp = Competencia.objects.create(programa=self.programa, nombre='C', tipo='especifica')
        momento = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=4, nombre='M1')
        evaluacion = EvaluacionFormal.objects.create(momento=momento, nombre='E', fecha_inicio=ahora, fecha_fin=ahora,
                                                     duracion_minutos=10, estado='publicada')
        ids = []
        for codigo in ('A1', 'A2'):
            asig = AsignaturaMalla.objects.create(codigo=codigo, nombre=f'Materia {codigo}', programa=self.programa)
            ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asig, descripcion='RA')
            p = PreguntaBanco.objects.create(asignatura=asig, resultado=ra, enunciado=codigo, opciones=['a', 'b'],
                                             respuesta_correcta=0, estado='aprobada')
            EvaluacionPregunta.objects.create(evaluacion=evaluacion, pregunta=p)
            ids.append(str(p.id))
        for email, respuestas in (('ana@t.co', {ids[0]: 0, ids[1]: 0}), ('beto@t.co', {ids[0]: 0, ids[1]: 1})):
            IntentoEvaluacion.objects.create(evaluacion=evaluacion, estudiante=_usuario(email, 'Estudiante'),
                                             vence_en=ahora, enviado_en=ahora, respuestas=respuestas)
        self.cliente = APIClient()
        self.cliente.force_authenticate(_usuario('vice@t.co', 'Vicerrector'))

    def test_indicadores_institucionales(self):
        datos = self.cliente.get(URL).data  # HU-11.1
        ind = datos['indicadores']
        self.assertEqual((ind['estudiantes'], ind['resultados'], ind['promedio']), (2, 4, 3.75))
        self.assertEqual((ind['por_encima'], ind['por_debajo']), (3, 1))
        self.assertEqual({d['rango']: d['cantidad'] for d in ind['distribucion']}['4–5'], 3)
        self.assertEqual([d['codigo'] for d in datos['desglose']], ['P1'])

    def test_drill_down_por_programa_y_materia(self):
        datos = self.cliente.get(URL, {'programa': self.programa.id}).data  # HU-11.2
        materias = {d['codigo']: d['promedio'] for d in datos['desglose']}
        self.assertEqual(materias, {'A1': 5.0, 'A2': 2.5})
        vacio = self.cliente.get(URL, {'programa': ProgramaAcademico.objects.get(codigo='P2').id}).data
        self.assertEqual((vacio['programa']['codigo'], vacio['indicadores']['resultados']), ('P2', 0))

    def test_exportar_pdf_y_excel(self):
        pdf = self.cliente.get(URL + 'exportar/', {'formato': 'pdf'})
        self.assertEqual(pdf.status_code, 200)  # HU-11.3
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        excel = self.cliente.get(URL + 'exportar/', {'formato': 'xlsx', 'programa': self.programa.id})
        self.assertEqual(excel.status_code, 200)
        self.assertTrue(excel.content.startswith(b'PK'))  # .xlsx es un ZIP
        self.assertIn('reporte_P1_', excel['Content-Disposition'])
        self.assertEqual(self.cliente.get(URL + 'exportar/', {'formato': 'doc'}).status_code, 400)

    def test_vicerrector_solo_lectura_y_acceso_por_rol(self):
        self.assertEqual(self.cliente.post(URL, {}).status_code, 403)
        self.assertEqual(self.cliente.get('/api/evaluacion/programas/').status_code, 403)  # no gestiona el catálogo
        self.cliente.force_authenticate(_usuario('admin@t.co', 'Administrador'))
        self.assertEqual(self.cliente.get(URL).status_code, 200)
        # ADR-015: el Coordinador lee el reporte (solo lectura); Docente y Estudiante no.
        for rol in ('Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
                self.assertEqual(self.cliente.get(URL).status_code, 403)
