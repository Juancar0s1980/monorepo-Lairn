"""Pruebas del centro de ayuda (ADR-018)."""

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import ArticuloAyuda
from apps.evaluacion_resultados.services.guias_ayuda import GUIAS, sembrar
from apps.evaluacion_resultados.tests.test_analitica_ra import _usuario

URL = '/api/evaluacion/ayuda/'
MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class PruebasAyuda(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        # La migración 0011 ya sembró las guías en la base de pruebas.
        self.cliente = APIClient()

    def como(self, rol):
        from apps.users.models import User

        email = f'{rol.lower()}@ayuda.co'
        self.cliente.force_authenticate(User.objects.filter(email=email).first() or _usuario(email, rol))

    def test_guias_iniciales_completas_e_idempotentes(self):
        self.assertEqual(ArticuloAyuda.objects.count(), len(GUIAS))
        self.assertEqual(sembrar(ArticuloAyuda), 0)
        for a in ArticuloAyuda.objects.all():
            with self.subTest(guia=a.slug):
                self.assertTrue(a.pasos and all(p['titulo'] for p in a.pasos))
                self.assertTrue(a.ruta.startswith('/'))
                self.assertFalse(a.video)  # no hay videos inventados

    def test_cada_rol_ve_sus_guias(self):
        self.como('Estudiante')
        r = self.cliente.get(URL)
        self.assertEqual(r.status_code, 200)
        slugs = {a['slug'] for a in r.data['articulos']}
        self.assertIn('presentar-evaluacion', slugs)
        self.assertIn('usar-centro-de-ayuda', slugs)  # sin rol = todos
        self.assertNotIn('crear-programa', slugs)
        self.assertFalse(r.data['puede_editar'])
        self.assertEqual(self.cliente.get(URL + 'crear-programa/').status_code, 404)
        self.como('Vicerrector')
        slugs = {a['slug'] for a in self.cliente.get(URL).data['articulos']}
        self.assertIn('informe-resultados-aprendizaje', slugs)
        self.assertNotIn('banco-de-preguntas', slugs)

    def test_busqueda_sin_tildes_y_categoria(self):
        self.como('Coordinador')
        r = self.cliente.get(URL, {'q': 'MOMENTO evaluacion'})
        slugs = [a['slug'] for a in r.data['articulos']]
        self.assertIn('momentos-de-evaluacion', slugs)
        self.assertNotIn('crear-programa', slugs)
        r = self.cliente.get(URL, {'categoria': 'docentes'})
        self.assertEqual({a['slug'] for a in r.data['articulos']},
                         {'asignar-docente-individual', 'asignar-docentes-masivo'})
        self.assertTrue(all(c['total'] > 0 for c in r.data['categorias']))
        self.assertEqual(self.cliente.get(URL, {'q': 'zzzz'}).data['articulos'], [])

    def test_no_publicada_solo_la_ve_el_administrador(self):
        ArticuloAyuda.objects.filter(slug='crear-programa').update(publicado=False)
        self.como('Coordinador')
        self.assertEqual(self.cliente.get(URL + 'crear-programa/').status_code, 404)
        self.como('Administrador')
        self.assertEqual(self.cliente.get(URL + 'crear-programa/').status_code, 200)

    def test_edicion_solo_administrador_y_validada(self):
        self.como('Coordinador')
        self.assertEqual(self.cliente.patch(URL + 'crear-programa/', {'resumen': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.cliente.post(URL, {'titulo': 'x'}, format='json').status_code, 403)
        self.como('Administrador')
        r = self.cliente.patch(URL + 'crear-programa/', {'resumen': 'Nuevo resumen',
                                                          'pasos': [{'titulo': 'Uno', 'detalle': 'd'}]}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.data['resumen'], r.data['pasos']), ('Nuevo resumen', [{'titulo': 'Uno', 'detalle': 'd'}]))
        for malo in ({'titulo': ''}, {'pasos': [{'detalle': 'sin título'}]}, {'roles': ['Rector']},
                     {'categoria': 'otra'}, {'ruta': 'http://fuera.com'}):
            with self.subTest(malo=malo):
                self.assertEqual(self.cliente.patch(URL + 'crear-programa/', malo, format='json').status_code, 400)
        r = self.cliente.post(URL, {'titulo': 'Crear programa académico', 'resumen': 'r', 'categoria': 'estructura'},
                              format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['slug'], 'crear-programa-academico')
        # La siembra no sobrescribe lo editado.
        sembrar(ArticuloAyuda)
        self.assertEqual(ArticuloAyuda.objects.get(slug='crear-programa').resumen, 'Nuevo resumen')

    def test_video_subir_ver_y_quitar(self):
        url = URL + 'presentar-evaluacion/video/'
        self.como('Estudiante')
        self.assertEqual(self.cliente.get(url).status_code, 404)  # aún sin video
        self.assertEqual(self.cliente.post(url, {'video': SimpleUploadedFile('v.mp4', b'x')}).status_code, 403)
        self.como('Administrador')
        self.assertEqual(self.cliente.post(url, {'video': SimpleUploadedFile('v.avi', b'x')}).status_code, 400)
        r = self.cliente.post(url, {'video': SimpleUploadedFile('guia.mp4', b'\x00\x00\x00\x18ftypmp42', 'video/mp4')})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['tiene_video'])
        self.como('Estudiante')
        r = self.cliente.get(url)
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'video/mp4'))
        self.assertEqual(b''.join(r.streaming_content), b'\x00\x00\x00\x18ftypmp42')
        self.assertIn(APIClient().get(url).status_code, (401, 403))  # sin sesión
        self.como('Administrador')
        self.assertFalse(self.cliente.delete(url).data['tiene_video'])
