"""
Pruebas del importador JSON (servicio + endpoints de integración).

Cubren: la vista previa coincide con la importación real, idempotencia,
duplicados, conflictos, preservación de datos existentes, huella y
permisos por rol.
"""

from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    ProgramaAcademico,
    RegistroSincronizacion,
    SemestrePrograma,
)
from apps.evaluacion_resultados.services.servicio_importador_nova import (
    ErrorImportacion,
    importar_programas_json,
)
from apps.users.models import Role, User

LOTE = {
    'programas': [
        {'codigo': 'ING-SIS', 'nombre': 'Ingeniería de Sistemas', 'duracion': 10, 'semestres': [1, 2]},
    ],
    'asignaturas': [
        {'codigo': 'SIS101', 'nombre': 'Programación I', 'creditos': 4,
         'programa_codigo': 'ING-SIS', 'semestre': 1},
    ],
}


def _acciones(resumen):
    return {(f['entidad'], f['clave']): f['accion'] for f in resumen['registros']}


class PruebasImportador(TestCase):
    def test_simulacro_no_escribe_y_coincide_con_real(self):
        previa = importar_programas_json(LOTE, modo='simulacro')
        self.assertEqual(ProgramaAcademico.objects.count(), 0)
        self.assertEqual((previa['creados'], previa['actualizados'], previa['rechazados']), (2, 0, 0))

        real = importar_programas_json(LOTE, modo='real', huella_esperada=previa['huella'])
        self.assertEqual(_acciones(real), _acciones(previa))
        programa = ProgramaAcademico.objects.get(codigo='ING-SIS')
        self.assertEqual(programa.duracion_semestres, 10)
        self.assertEqual(SemestrePrograma.objects.filter(programa=programa).count(), 2)
        self.assertEqual(AsignaturaMalla.objects.get(codigo='SIS101').semestre.numero, 1)

    def test_idempotente_sin_duplicar(self):
        importar_programas_json(LOTE, modo='real')
        segunda = importar_programas_json(LOTE, modo='real')
        self.assertEqual((segunda['creados'], segunda['actualizados']), (0, 2))
        self.assertEqual(ProgramaAcademico.objects.count(), 1)
        self.assertEqual(AsignaturaMalla.objects.count(), 1)

    def test_codigo_sin_distinguir_mayusculas(self):
        ProgramaAcademico.objects.create(codigo='ing-sis', nombre='Manual', duracion_semestres=9)
        resumen = importar_programas_json(LOTE, modo='real')
        self.assertEqual(_acciones(resumen)[('programa', 'ING-SIS')], 'actualizar')
        self.assertEqual(ProgramaAcademico.objects.count(), 1)

    def test_actualizar_conserva_campos_ausentes_y_estado(self):
        ProgramaAcademico.objects.create(
            codigo='ING-SIS', nombre='Viejo', duracion_semestres=9, sede='Norte', activo=False,
        )
        importar_programas_json({'programas': [{'codigo': 'ING-SIS', 'nombre': 'Nuevo'}]}, modo='real')
        programa = ProgramaAcademico.objects.get(codigo='ING-SIS')
        self.assertEqual((programa.nombre, programa.duracion_semestres, programa.sede), ('Nuevo', 9, 'Norte'))
        self.assertFalse(programa.activo)  # un programa desactivado no se reactiva

    def test_rechaza_tipos_invalidos_y_duplicados(self):
        resumen = importar_programas_json({
            'programas': [
                {'codigo': 'A', 'nombre': 'A', 'duracion': 'ocho'},
                {'codigo': 'B', 'nombre': 'B', 'duracion': 40},
                {'codigo': 'C'},
                {'codigo': 'D', 'nombre': 'D'},
                {'codigo': 'd', 'nombre': 'D otra vez'},
            ],
            'asignaturas': [
                {'codigo': 'X1', 'nombre': 'X', 'programa_codigo': 'A'},
                {'codigo': 'X2', 'nombre': 'X', 'programa_codigo': 'NOEXISTE'},
                {'codigo': 'X3', 'nombre': 'X', 'programa_codigo': 'D', 'tipo': 'rara'},
                {'codigo': 'X4', 'nombre': 'X', 'programa_codigo': 'D', 'semestre': 12},
            ],
        }, modo='simulacro')
        self.assertEqual(resumen['creados'], 1)  # solo el programa D
        self.assertEqual(resumen['rechazados'], 8)
        self.assertTrue(all(f['motivo'] for f in resumen['registros'] if f['accion'] == 'rechazar'))

    def test_asignatura_de_otro_programa_no_se_mueve(self):
        otro = ProgramaAcademico.objects.create(codigo='OTRO', nombre='Otro')
        AsignaturaMalla.objects.create(codigo='SIS101', nombre='Ajena', programa=otro)
        resumen = importar_programas_json(LOTE, modo='real')
        self.assertEqual(_acciones(resumen)[('asignatura', 'SIS101')], 'rechazar')
        self.assertEqual(AsignaturaMalla.objects.get(codigo='SIS101').programa, otro)

    def test_usuarios_nunca_se_crean(self):
        User.objects.create_user(email='ya@u.edu.co', password='x', first_name='Y', first_last_name='A')
        resumen = importar_programas_json(
            {'usuarios': [{'email': 'ya@u.edu.co'}, {'email': 'nuevo@u.edu.co'}]}, modo='real',
        )
        self.assertEqual((resumen['sin_cambios'], resumen['omitidos']), (1, 1))
        self.assertFalse(User.objects.filter(email='nuevo@u.edu.co').exists())

    def test_huella_distinta_bloquea(self):
        with self.assertRaises(ErrorImportacion) as ctx:
            importar_programas_json(LOTE, modo='real', huella_esperada='0' * 64)
        self.assertEqual(ctx.exception.estado, 409)
        self.assertEqual(ProgramaAcademico.objects.count(), 0)

    def test_estructura_invalida(self):
        for payload in ([], {'programas': 'x'}, {}, {'otra': []}):
            with self.subTest(payload=payload), self.assertRaises(ErrorImportacion):
                importar_programas_json(payload)

    def test_fallo_de_escritura_no_deja_cambios(self):
        with mock.patch.object(AsignaturaMalla.objects, 'create', side_effect=RuntimeError('bd')):
            with self.assertRaises(ErrorImportacion) as ctx:
                importar_programas_json(LOTE, modo='real')
        self.assertEqual(ctx.exception.estado, 500)
        self.assertEqual(ProgramaAcademico.objects.count(), 0)  # rollback del programa
        self.assertTrue(RegistroSincronizacion.objects.filter(modo='real_fallido').exists())


class PruebasEndpoints(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.admin = User.objects.create_user(
            email='admin@t.co', password='x', first_name='A', first_last_name='B',
            role=Role.objects.create(name='Administrador'),
        )
        self.docente = User.objects.create_user(
            email='doc@t.co', password='x', first_name='D', first_last_name='B',
            role=Role.objects.create(name='Docente'),
        )

    def test_solo_administrador(self):
        self.cliente.force_authenticate(self.docente)
        for ruta, cuerpo in (('importar-url', {'url': 'https://e.com/a.json'}), ('importar-json', {'datos': LOTE})):
            with self.subTest(ruta=ruta):
                r = self.cliente.post(f'/api/evaluacion/integracion/{ruta}/', cuerpo, format='json')
                self.assertEqual(r.status_code, 403)

    def test_url_interna_rechazada_con_mensaje_claro(self):
        self.cliente.force_authenticate(self.admin)
        r = self.cliente.post('/api/evaluacion/integracion/importar-url/',
                              {'url': 'https://127.0.0.1/a.json'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('red interna', r.data['detalle'])

    def test_url_real_exige_validacion_previa(self):
        self.cliente.force_authenticate(self.admin)
        r = self.cliente.post('/api/evaluacion/integracion/importar-url/',
                              {'url': 'https://e.com/a.json', 'modo': 'real'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('huella', r.data)

    def test_flujo_url_validar_y_confirmar(self):
        self.cliente.force_authenticate(self.admin)
        ruta = 'apps.evaluacion_resultados.views.administrador.vista_integracion_nova.obtener_json_desde_url'
        with mock.patch(ruta, return_value=LOTE):
            previa = self.cliente.post('/api/evaluacion/integracion/importar-url/',
                                       {'url': 'https://e.com/a.json'}, format='json')
            self.assertEqual(previa.status_code, 200)
            self.assertEqual(ProgramaAcademico.objects.count(), 0)
            real = self.cliente.post('/api/evaluacion/integracion/importar-url/', {
                'url': 'https://e.com/a.json', 'modo': 'real', 'huella': previa.data['huella'],
            }, format='json')
        self.assertEqual(real.status_code, 200)
        self.assertEqual(real.data['origen'], 'json_url')
        self.assertEqual(ProgramaAcademico.objects.count(), 1)

    def test_importar_json_contrato_previo(self):
        self.cliente.force_authenticate(self.admin)
        r = self.cliente.post('/api/evaluacion/integracion/importar-json/',
                              {'datos': LOTE, 'modo': 'simulacro'}, format='json')
        self.assertEqual(r.status_code, 200)
        for campo in ('registro_id', 'modo', 'total_recibidos', 'creados', 'actualizados', 'omitidos', 'errores'):
            self.assertIn(campo, r.data)
