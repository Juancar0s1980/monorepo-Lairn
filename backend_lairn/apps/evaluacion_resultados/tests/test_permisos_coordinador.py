"""
Permisos del rol Coordinador sobre la configuración académica.

Backlog: el Coordinador consulta programas (HU-01.3) y gestiona semestres,
asignaturas, competencias, RA y momentos (HU-01.4 a HU-02.3). Crear/editar
programas (HU-01.1/01.2) e importar datos (HU-03) siguen siendo del
Administrador. Docente y Estudiante no acceden.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.users.models import Role, User

BASE = '/api/evaluacion'


def _usuario(rol: str) -> User:
    return User.objects.create_user(
        email=f'{rol.lower()}@t.co', password='x', first_name=rol, first_last_name='P',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class PruebasPermisosCoordinador(TestCase):
    def setUp(self):
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Programa 1', duracion_semestres=8)
        self.cliente = APIClient()

    def _como(self, rol: str):
        self.cliente.force_authenticate(_usuario(rol))

    def test_coordinador_consulta_programas_pero_no_los_crea_ni_edita(self):
        self._como('Coordinador')
        self.assertEqual(self.cliente.get(f'{BASE}/programas/').status_code, 200)
        self.assertEqual(self.cliente.get(f'{BASE}/programas/{self.programa.id}/').status_code, 200)
        crear = self.cliente.post(f'{BASE}/programas/', {'codigo': 'P2', 'nombre': 'X', 'duracion_semestres': 8}, format='json')
        editar = self.cliente.patch(f'{BASE}/programas/{self.programa.id}/', {'nombre': 'Y'}, format='json')
        self.assertEqual((crear.status_code, editar.status_code), (403, 403))

    def test_coordinador_gestiona_estructura_curricular(self):
        self._como('Coordinador')
        p = self.programa.id
        semestre = self.cliente.post(f'{BASE}/programas/{p}/semestres/', {'numero': 1}, format='json')
        self.assertEqual(semestre.status_code, 201, semestre.data)
        competencia = self.cliente.post(f'{BASE}/programas/{p}/competencias/',
                                        {'nombre': 'Diseño', 'tipo': 'transversal'}, format='json')
        self.assertEqual(competencia.status_code, 201, competencia.data)
        momento = self.cliente.post(f'{BASE}/programas/{p}/momentos/', {'nombre': 'Corte 1'}, format='json')
        # Solo se prueba el permiso: un 400 sería validación de negocio del momento.
        self.assertNotIn(momento.status_code, (401, 403))
        self.assertEqual(self.cliente.get(f'{BASE}/programas/{p}/tablero/').status_code, 200)

    def test_coordinador_no_importa_ni_carga_documentos(self):
        self._como('Coordinador')
        for metodo, ruta in (('post', 'integracion/importar-json/'), ('post', 'integracion/importar-url/'),
                             ('get', 'integracion/registros/'), ('get', 'cargues/')):
            with self.subTest(ruta=ruta):
                self.assertEqual(getattr(self.cliente, metodo)(f'{BASE}/{ruta}', {}, format='json').status_code, 403)

    def test_docente_y_estudiante_sin_acceso(self):
        for rol in ('Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self._como(rol)
                self.assertEqual(self.cliente.get(f'{BASE}/programas/').status_code, 403)
                self.assertEqual(self.cliente.get(f'{BASE}/programas/{self.programa.id}/semestres/').status_code, 403)

    def test_administrador_conserva_todo(self):
        self._como('Administrador')
        crear = self.cliente.post(f'{BASE}/programas/', {'codigo': 'P2', 'nombre': 'X', 'duracion_semestres': 8}, format='json')
        self.assertEqual(crear.status_code, 201, crear.data)
        self.assertEqual(self.cliente.get(f'{BASE}/cargues/').status_code, 200)
