"""
Tests de aislamiento entre docentes y de acceso por inscripción para
estudiantes. El patrón del proyecto (`Curso.objects.get(id=..., docente=request.user)`,
`Examen.objects.get(id=..., curso__docente=request.user)`) hace que "no es
tuyo" y "no existe" respondan exactamente igual (404) a propósito, para no
filtrar si un curso/examen ajeno existe — eso es justo lo que se verifica
acá.
"""

from rest_framework.test import APITestCase

from apps.examenes.models import Examen
from core.tests.utils import crear_curso, crear_docente, crear_estudiante, inscribir


class AislamientoEntreDocentesTests(APITestCase):
    def setUp(self):
        self.docente_dueno = crear_docente(email='dueno@test.com')
        self.docente_intruso = crear_docente(email='intruso@test.com')
        self.curso = crear_curso(self.docente_dueno)
        self.examen = Examen.objects.create(
            curso=self.curso, titulo='Examen ajeno', tema='Álgebra', tiempo=30, num_preguntas=5,
        )

    def test_dueno_puede_ver_su_propio_curso(self):
        self.client.force_authenticate(user=self.docente_dueno)
        resp = self.client.get(f'/api/examenes/cursos/{self.curso.id}/')
        self.assertEqual(resp.status_code, 200)

    def test_otro_docente_no_puede_ver_curso_ajeno(self):
        self.client.force_authenticate(user=self.docente_intruso)
        resp = self.client.get(f'/api/examenes/cursos/{self.curso.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_otro_docente_no_puede_editar_curso_ajeno(self):
        self.client.force_authenticate(user=self.docente_intruso)
        resp = self.client.patch(f'/api/examenes/cursos/{self.curso.id}/', {'nombre': 'Secuestrado'})
        self.assertEqual(resp.status_code, 404)
        self.curso.refresh_from_db()
        self.assertNotEqual(self.curso.nombre, 'Secuestrado')

    def test_otro_docente_no_puede_eliminar_curso_ajeno(self):
        self.client.force_authenticate(user=self.docente_intruso)
        resp = self.client.delete(f'/api/examenes/cursos/{self.curso.id}/')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(self.curso.__class__.objects.filter(id=self.curso.id).exists())

    def test_otro_docente_no_puede_ver_examen_ajeno(self):
        self.client.force_authenticate(user=self.docente_intruso)
        resp = self.client.get(f'/api/examenes/examenes/{self.examen.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_otro_docente_no_puede_eliminar_examen_ajeno(self):
        self.client.force_authenticate(user=self.docente_intruso)
        resp = self.client.delete(f'/api/examenes/examenes/{self.examen.id}/')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Examen.objects.filter(id=self.examen.id).exists())


class AccesoPorInscripcionTests(APITestCase):
    def setUp(self):
        docente = crear_docente()
        self.curso = crear_curso(docente)
        Examen.objects.create(curso=self.curso, titulo='Examen', tema='Cálculo', tiempo=30, num_preguntas=5)
        self.estudiante_inscrito = crear_estudiante(email='inscrito@test.com')
        self.estudiante_no_inscrito = crear_estudiante(email='no-inscrito@test.com')
        inscribir(self.estudiante_inscrito, self.curso)

    def test_estudiante_inscrito_ve_los_examenes_del_curso(self):
        self.client.force_authenticate(user=self.estudiante_inscrito)
        resp = self.client.get(f'/api/examenes/mis-cursos/{self.curso.id}/examenes/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_estudiante_no_inscrito_recibe_403(self):
        self.client.force_authenticate(user=self.estudiante_no_inscrito)
        resp = self.client.get(f'/api/examenes/mis-cursos/{self.curso.id}/examenes/')
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_usar_endpoints_de_estudiante(self):
        docente = crear_docente(email='otro-docente@test.com')
        self.client.force_authenticate(user=docente)
        resp = self.client.get(f'/api/examenes/mis-cursos/{self.curso.id}/examenes/')
        self.assertEqual(resp.status_code, 403)
