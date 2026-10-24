from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from apps.users.models.user import User


class SolicitarRecuperacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            email='estudiante@pseudotutor.com',
            password='ClaveVieja1234*',
            first_name='Ana',
            first_last_name='Pérez',
        )

    @patch('apps.users.views.vista_solicitar_recuperacion.enviar_correo_recuperacion')
    def test_correo_existente_envia_correo_y_responde_generico(self, mock_enviar):
        respuesta = self.client.post(
            '/api/usuarios/recuperar-contrasena/', {'email': 'estudiante@pseudotutor.com'}
        )
        self.assertEqual(respuesta.status_code, 200)
        mock_enviar.assert_called_once()
        self.assertEqual(mock_enviar.call_args[0][0], self.usuario)

    @patch('apps.users.views.vista_solicitar_recuperacion.enviar_correo_recuperacion')
    def test_correo_inexistente_no_envia_pero_responde_igual(self, mock_enviar):
        respuesta = self.client.post(
            '/api/usuarios/recuperar-contrasena/', {'email': 'no-existe@pseudotutor.com'}
        )
        self.assertEqual(respuesta.status_code, 200)
        mock_enviar.assert_not_called()

    def test_email_invalido_responde_400(self):
        respuesta = self.client.post('/api/usuarios/recuperar-contrasena/', {'email': 'no-es-un-correo'})
        self.assertEqual(respuesta.status_code, 400)


class RestablecerContrasenaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            email='estudiante@pseudotutor.com',
            password='ClaveVieja1234*',
            first_name='Ana',
            first_last_name='Pérez',
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        self.token = default_token_generator.make_token(self.usuario)

    def test_token_valido_cambia_la_contrasena(self):
        respuesta = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': self.uid,
            'token': self.token,
            'password': 'ClaveNueva5678*',
        })
        self.assertEqual(respuesta.status_code, 200)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveNueva5678*'))
        self.assertFalse(self.usuario.check_password('ClaveVieja1234*'))

    def test_token_invalido_responde_400_y_no_cambia_nada(self):
        respuesta = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': self.uid,
            'token': 'token-invalido',
            'password': 'ClaveNueva5678*',
        })
        self.assertEqual(respuesta.status_code, 400)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveVieja1234*'))

    def test_token_ya_usado_no_se_puede_reusar(self):
        primera = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': self.uid,
            'token': self.token,
            'password': 'ClaveNueva5678*',
        })
        self.assertEqual(primera.status_code, 200)

        segunda = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': self.uid,
            'token': self.token,
            'password': 'OtraClave9012*',
        })
        self.assertEqual(segunda.status_code, 400)

    def test_contrasena_debil_responde_400(self):
        respuesta = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': self.uid,
            'token': self.token,
            'password': '1234',
        })
        self.assertEqual(respuesta.status_code, 400)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveVieja1234*'))

    def test_uid_invalido_responde_400(self):
        respuesta = self.client.post('/api/usuarios/restablecer-contrasena/', {
            'uid': 'uid-invalido',
            'token': self.token,
            'password': 'ClaveNueva5678*',
        })
        self.assertEqual(respuesta.status_code, 400)
