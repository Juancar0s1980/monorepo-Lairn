"""Pruebas de la solicitud de vinculación curso ↔ asignatura de la malla (HU-01.10)."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import AsignaturaMalla, ProgramaAcademico, SolicitudVinculacion
from apps.examenes.models import Curso
from apps.users.models import Role, User

URL = '/api/evaluacion'


def _u(email, rol):
    return User.objects.create_user(email=email, password='x', first_name='N', first_last_name='A',
                                    role=Role.objects.get_or_create(name=rol)[0])


class PruebasVinculacion(TestCase):
    def setUp(self):
        self.docente = _u('doc@t.co', 'Docente')
        self.otro_docente = _u('doc2@t.co', 'Docente')
        self.coord = _u('coord@t.co', 'Coordinador')
        self.curso = Curso.objects.create(nombre='Bioquímica 2026-2', docente=self.docente)
        self.curso_ajeno = Curso.objects.create(nombre='Otro', docente=self.otro_docente)
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Entrenamiento')
        self.asig = AsignaturaMalla.objects.create(codigo='A1', nombre='Bioquímica', programa=programa)
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.docente)

    def pedir(self, curso=None, asignatura=None, mensaje='Soy el docente asignado este semestre.'):
        return self.cliente.post(f'{URL}/docente/cursos/{(curso or self.curso).id}/vinculacion/',
                                 {'asignatura': (asignatura or self.asig).id, 'mensaje': mensaje}, format='json')

    def test_docente_pide_y_ve_estado(self):
        opciones = self.cliente.get(f'{URL}/vinculacion/opciones/').data
        self.assertEqual(opciones[0]['asignaturas'][0]['codigo'], 'A1')
        r = self.pedir()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['estado'], 'pendiente')
        self.assertEqual(self.pedir().status_code, 409)  # sin duplicar pendientes
        estado = self.cliente.get(f'{URL}/docente/cursos/{self.curso.id}/vinculacion/').data
        self.assertEqual(len(estado['solicitudes']), 1)
        self.assertEqual(estado['vinculadas'], [])

    def test_solo_sus_cursos_y_solo_gestores_resuelven(self):
        self.assertEqual(self.pedir(curso=self.curso_ajeno).status_code, 404)
        sid = self.pedir().data['id']
        self.assertEqual(self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid}/aprobar/').status_code, 403)
        self.assertEqual(self.cliente.get(f'{URL}/vinculacion/solicitudes/').status_code, 403)
        estudiante = _u('est@t.co', 'Estudiante')
        self.cliente.force_authenticate(estudiante)
        self.assertEqual(self.cliente.get(f'{URL}/vinculacion/opciones/').status_code, 403)

    def test_aprobar_vincula_y_reemplaza_con_trazabilidad(self):
        self.asig.curso_vinculado = self.curso_ajeno
        self.asig.save()
        sid = self.pedir().data['id']
        self.cliente.force_authenticate(self.coord)
        bandeja = self.cliente.get(f'{URL}/vinculacion/solicitudes/').data
        self.assertEqual(bandeja['pendientes'], 1)
        r = self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid}/aprobar/', {}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.curso_vinculado_id, self.curso.id)
        self.assertIn('Otro', r.data['reemplazo_curso'])
        self.assertEqual(self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid}/aprobar/').status_code, 409)

    def test_rechazar_exige_motivo_y_cancelar(self):
        sid = self.pedir().data['id']
        self.cliente.force_authenticate(self.coord)
        self.assertEqual(self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid}/rechazar/', {}, format='json').status_code, 400)
        r = self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid}/rechazar/', {'respuesta': 'La dicta otro docente.'}, format='json')
        self.assertEqual(r.data['estado'], 'rechazada')
        self.cliente.force_authenticate(self.docente)
        sid2 = self.pedir().data['id']
        self.assertEqual(self.cliente.post(f'{URL}/vinculacion/solicitudes/{sid2}/cancelar/').data['estado'], 'cancelada')
        self.assertEqual(SolicitudVinculacion.objects.filter(estado='pendiente').count(), 0)

    def test_aprobar_una_cierra_las_demas_pendientes_de_la_asignatura(self):
        s1 = self.pedir().data['id']
        self.cliente.force_authenticate(self.otro_docente)
        s2 = self.pedir(curso=self.curso_ajeno).data['id']
        self.cliente.force_authenticate(self.coord)
        self.cliente.post(f'{URL}/vinculacion/solicitudes/{s1}/aprobar/', {}, format='json')
        self.assertEqual(SolicitudVinculacion.objects.get(pk=s2).estado, 'rechazada')
