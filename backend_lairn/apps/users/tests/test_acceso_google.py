"""
Pruebas del inicio de sesión con Google institucional (HU-26).

La verificación criptográfica la hace google-auth contra Google; aquí se simula su resultado
para probar todas las reglas del sistema sin depender de la red.
"""

from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import IdentidadGoogle, Role, User

URL = '/api/usuarios'
PARCHE = 'apps.users.services.autenticacion_google.verificar_token_google'
CONF = dict(GOOGLE_CLIENT_ID='cliente-prueba.apps.googleusercontent.com', DOMINIOS_INSTITUCIONALES=['uniautonoma.edu.co'])


def token(email='brayner.trochez.o@uniautonoma.edu.co', sub='1001', hd='uniautonoma.edu.co', verificado=True, iss='https://accounts.google.com'):
    return {'email': email, 'sub': sub, 'hd': hd, 'email_verified': verificado, 'iss': iss}


@override_settings(**CONF, AUTENTICACION_SOLO_INSTITUCIONAL=True)
class PruebasAccesoGoogle(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.rol = Role.objects.get_or_create(name='Docente')[0]
        self.usuario = User.objects.create_user(email='brayner.trochez.o@uniautonoma.edu.co', password=None,
                                                first_name='Brayner', first_last_name='Trochez', role=self.rol)

    def entrar(self, datos=None, error=None):
        efecto = {'side_effect': error} if error else {'return_value': datos or token()}
        with mock.patch(PARCHE, **efecto):
            return self.cliente.post(f'{URL}/iniciar-sesion-google/', {'credential': 'x.y.z'}, format='json')

    def test_ingreso_institucional_emite_tokens_con_rol(self):
        r = self.entrar()
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn('access', r.data)
        self.cliente.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
        self.assertEqual(self.cliente.get(f'{URL}/mis-datos/').status_code, 200)
        self.assertEqual(IdentidadGoogle.objects.get(usuario=self.usuario).sub, '1001')

    def test_rechaza_correo_no_institucional_y_sin_hd(self):
        self.assertEqual(self.entrar(token(email='alguien@gmail.com', hd='')).data['codigo'], 'no_institucional')
        # Correo institucional pero emitido fuera del Workspace (sin hd): también se rechaza.
        self.assertEqual(self.entrar(token(hd='')).data['codigo'], 'no_institucional')

    def test_rechaza_token_invalido_y_correo_no_verificado(self):
        self.assertEqual(self.entrar(error=ValueError('firma')).status_code, 401)
        self.assertEqual(self.entrar(token(iss='https://evil.example')).status_code, 401)
        self.assertEqual(self.entrar(token(verificado=False)).data['codigo'], 'correo_no_verificado')

    def test_sin_cuenta_y_cuenta_desactivada(self):
        self.assertEqual(self.entrar(token(email='nuevo.o@uniautonoma.edu.co')).data['codigo'], 'sin_cuenta')
        self.usuario.is_active = False
        self.usuario.save()
        r = self.entrar()
        self.assertEqual((r.status_code, r.data['codigo']), (403, 'cuenta_inactiva'))

    def test_desactivar_invalida_la_sesion_vigente(self):
        tokens = self.entrar().data
        self.usuario.is_active = False
        self.usuario.save()
        self.cliente.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(self.cliente.get(f'{URL}/mis-datos/').status_code, 401)
        self.cliente.credentials()
        self.assertEqual(self.cliente.post(f'{URL}/token/actualizar/', {'refresh': tokens['refresh']}, format='json').status_code, 401)

    def test_identidad_distinta_para_el_mismo_correo(self):
        self.entrar()
        self.assertEqual(self.entrar(token(sub='2002')).data['codigo'], 'identidad_distinta')

    def test_solo_institucional_cierra_contrasena_registro_y_recuperacion(self):
        for ruta, datos in (('iniciar-sesion', {'email': 'a@b.co', 'password': 'x'}), ('registrar', {}),
                            ('recuperar-contrasena', {'email': 'a@b.co'}), ('restablecer-contrasena', {})):
            with self.subTest(ruta=ruta):
                r = self.cliente.post(f'{URL}/{ruta}/', datos, format='json')
                self.assertEqual((r.status_code, r.data['codigo']), (403, 'solo_institucional'))
        config = self.cliente.get(f'{URL}/config-acceso/').data
        self.assertTrue(config['solo_institucional'])
        self.assertEqual(config['dominios'], ['uniautonoma.edu.co'])

    @override_settings(GOOGLE_CLIENT_ID='')
    def test_sin_configurar(self):
        self.assertEqual(self.entrar().status_code, 503)


@override_settings(**CONF)
class PruebasAltaCuentas(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.admin = User.objects.create_user(email='admin@x.co', password='x', first_name='A', first_last_name='B',
                                              role=Role.objects.get_or_create(name='Administrador')[0])
        self.rol = Role.objects.get_or_create(name='Estudiante')[0]
        self.cliente.force_authenticate(self.admin)

    def crear(self, **extra):
        datos = {'email': 'laura.solarte.m@uniautonoma.edu.co', 'first_name': 'Laura', 'first_last_name': 'Solarte',
                 'role_id': self.rol.id, **extra}
        return self.cliente.post(f'{URL}/administracion/usuarios/', datos, format='json')

    @override_settings(AUTENTICACION_SOLO_INSTITUCIONAL=True)
    def test_admin_crea_cuenta_institucional_sin_contrasena(self):
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        u = User.objects.get(email='laura.solarte.m@uniautonoma.edu.co')
        self.assertFalse(u.has_usable_password())
        self.assertEqual(self.crear().status_code, 400)  # duplicado
        self.assertIn('email', self.crear(email='laura@gmail.com').data)  # no institucional

    def test_solo_el_administrador_crea_cuentas(self):
        otro = User.objects.create_user(email='doc@x.co', password='x', first_name='D', first_last_name='D',
                                        role=Role.objects.get_or_create(name='Docente')[0])
        self.cliente.force_authenticate(otro)
        self.assertEqual(self.crear().status_code, 403)
