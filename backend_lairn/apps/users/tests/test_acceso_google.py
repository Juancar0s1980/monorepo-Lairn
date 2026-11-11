"""
Pruebas del inicio de sesión con Google institucional (HU-26).

La verificación criptográfica la hace google-auth contra Google; aquí se simula su resultado
para probar todas las reglas del sistema sin depender de la red.
"""

from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import IdentidadGoogle, Role, SolicitudCuenta, User

URL = '/api/usuarios'
PARCHE = 'apps.users.services.autenticacion_google.verificar_token_google'
CONF = dict(GOOGLE_CLIENT_ID='cliente-prueba.apps.googleusercontent.com', DOMINIOS_INSTITUCIONALES=['uniautonoma.edu.co'],
            ADMINISTRADORES_INICIALES=[])


def token(email='brayner.trochez.o@uniautonoma.edu.co', sub='1001', hd='uniautonoma.edu.co', verificado=True, iss='https://accounts.google.com'):
    return {'email': email, 'sub': sub, 'hd': hd, 'email_verified': verificado, 'iss': iss,
            'given_name': 'Laura Valentina', 'family_name': 'Solarte Muñoz'}


def crear_roles():
    nombres = ('Administrador', 'Docente', 'Estudiante', 'Coordinador', 'Vicerrector')
    return {n: Role.objects.get_or_create(name=n)[0] for n in nombres}


@override_settings(**CONF, AUTENTICACION_SOLO_INSTITUCIONAL=True)
class PruebasAccesoGoogle(TestCase):
    def setUp(self):
        cache.clear()  # el límite de intentos de acceso se guarda en caché
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

    def test_cuenta_desactivada(self):
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
        cache.clear()  # el límite de intentos de acceso se guarda en caché
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


@override_settings(**{**CONF, 'ADMINISTRADORES_INICIALES': ['jefe.ti@uniautonoma.edu.co']}, AUTENTICACION_SOLO_INSTITUCIONAL=True)
class PruebasAltaPorPortal(TestCase):
    """Primer ingreso con Google: la cuenta se crea según el acceso (estudiantes o personal) y el rol."""

    def setUp(self):
        cache.clear()  # el límite de intentos de acceso se guarda en caché
        self.cliente = APIClient()
        self.roles = crear_roles()

    def entrar(self, email, sub, **extra):
        with mock.patch(PARCHE, return_value=token(email=email, sub=sub)):
            return self.cliente.post(f'{URL}/iniciar-sesion-google/', {'credential': 'x.y.z', **extra}, format='json')

    def test_estudiante_se_crea_activo_con_nombres_de_google(self):
        r = self.entrar('laura.solarte.m@uniautonoma.edu.co', '11', portal='estudiantes', rol='Administrador')
        self.assertEqual(r.status_code, 200, r.data)
        u = User.objects.get(email='laura.solarte.m@uniautonoma.edu.co')
        self.assertEqual((u.role.name, u.is_active, u.has_usable_password()), ('Estudiante', True, False))
        self.assertEqual((u.first_name, u.second_name, u.first_last_name, u.second_last_name),
                         ('Laura', 'Valentina', 'Solarte', 'Muñoz'))
        # El segundo ingreso reutiliza la cuenta.
        self.assertEqual(self.entrar('laura.solarte.m@uniautonoma.edu.co', '11').status_code, 200)
        self.assertEqual(User.objects.filter(email='laura.solarte.m@uniautonoma.edu.co').count(), 1)

    def test_docente_entra_sin_aprobacion(self):
        r = self.entrar('profe.x@uniautonoma.edu.co', '12', portal='personal', rol='Docente')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(User.objects.get(email='profe.x@uniautonoma.edu.co').role.name, 'Docente')

    def test_personal_debe_elegir_rol(self):
        self.assertEqual(self.entrar('a.b@uniautonoma.edu.co', '13', portal='personal').data['codigo'], 'rol_requerido')
        r = self.entrar('a.b@uniautonoma.edu.co', '13', portal='personal', rol='Estudiante')
        self.assertEqual(r.data['codigo'], 'rol_requerido')
        self.assertFalse(User.objects.filter(email='a.b@uniautonoma.edu.co').exists())

    def test_rol_administrativo_queda_pendiente_hasta_aprobar(self):
        for i, rol in enumerate(('Coordinador', 'Vicerrector', 'Administrador')):
            with self.subTest(rol=rol):
                correo = f'persona{i}@uniautonoma.edu.co'
                r = self.entrar(correo, f'2{i}', portal='personal', rol=rol)
                self.assertEqual((r.status_code, r.data['codigo']), (202, 'solicitud_enviada'))
                u = User.objects.get(email=correo)
                self.assertEqual((u.is_active, u.role), (False, None))
                self.assertEqual(SolicitudCuenta.objects.get(usuario=u).rol_solicitado.name, rol)
                r = self.entrar(correo, f'2{i}', portal='personal', rol=rol)
                self.assertEqual((r.status_code, r.data['codigo']), (403, 'cuenta_pendiente'))

    def test_aprobar_y_rechazar_solicitud(self):
        jefe = self.entrar('jefe.ti@uniautonoma.edu.co', '1', portal='estudiantes')
        self.assertEqual(jefe.status_code, 200)
        self.assertEqual(User.objects.get(email='jefe.ti@uniautonoma.edu.co').role.name, 'Administrador')
        self.entrar('coord@uniautonoma.edu.co', '31', portal='personal', rol='Coordinador')
        self.entrar('vice@uniautonoma.edu.co', '32', portal='personal', rol='Vicerrector')

        admin = APIClient()
        admin.credentials(HTTP_AUTHORIZATION=f'Bearer {jefe.data["access"]}')
        lista = admin.get(f'{URL}/administracion/solicitudes-cuenta/').data
        self.assertEqual(lista['pendientes'], 2)
        ids = {x['usuario']['email']: x['id'] for x in lista['solicitudes']}

        r = admin.post(f'{URL}/administracion/solicitudes-cuenta/{ids["coord@uniautonoma.edu.co"]}/aprobar/', {}, format='json')
        self.assertEqual(r.data['estado'], 'aprobada')
        ok = self.entrar('coord@uniautonoma.edu.co', '31', portal='personal')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(User.objects.get(email='coord@uniautonoma.edu.co').role.name, 'Coordinador')

        url_rechazo = f'{URL}/administracion/solicitudes-cuenta/{ids["vice@uniautonoma.edu.co"]}/rechazar/'
        self.assertEqual(admin.post(url_rechazo, {}, format='json').status_code, 400)  # motivo obligatorio
        self.assertEqual(admin.post(url_rechazo, {'motivo': 'No figura en nómina'}, format='json').status_code, 200)
        r = self.entrar('vice@uniautonoma.edu.co', '32', portal='personal')
        self.assertEqual(r.data['codigo'], 'solicitud_rechazada')
        self.assertIn('No figura en nómina', r.data['detalle'])
        self.assertEqual(admin.post(url_rechazo, {'motivo': 'x'}, format='json').status_code, 409)

        # Solo el Administrador ve y resuelve solicitudes.
        coord = APIClient()
        coord.credentials(HTTP_AUTHORIZATION=f'Bearer {ok.data["access"]}')
        self.assertEqual(coord.get(f'{URL}/administracion/solicitudes-cuenta/').status_code, 403)

    def test_administrador_inicial_existente_queda_como_administrador(self):
        User.objects.create_user(email='jefe.ti@uniautonoma.edu.co', password=None, first_name='J', first_last_name='T',
                                 role=self.roles['Estudiante'], is_active=False)
        r = self.entrar('jefe.ti@uniautonoma.edu.co', '41')
        self.assertEqual(r.status_code, 200, r.data)
        u = User.objects.get(email='jefe.ti@uniautonoma.edu.co')
        self.assertEqual((u.role.name, u.is_active), ('Administrador', True))

    def test_config_acceso_lista_roles_de_personal(self):
        roles = self.cliente.get(f'{URL}/config-acceso/').data['roles_personal']
        self.assertEqual({r['rol']: r['requiere_aprobacion'] for r in roles},
                         {'Docente': False, 'Coordinador': True, 'Vicerrector': True, 'Administrador': True})
