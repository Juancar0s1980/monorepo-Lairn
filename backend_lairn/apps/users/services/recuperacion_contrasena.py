"""
Recuperación de contraseña vía correo.

Usa el generador de tokens propio de Django (`default_token_generator`):
stateless, con expiración automática (`PASSWORD_RESET_TIMEOUT`, 3 días por
defecto) y firmado con el `SECRET_KEY` del proyecto — no hace falta ninguna
tabla nueva para guardar tokens de un solo uso, es exactamente el mismo
mecanismo que usa el flujo de "restablecer contraseña" del admin de Django.
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.users.models.user import User
from core.email.enviar_email import enviar_email

logger = logging.getLogger(__name__)


def enviar_correo_recuperacion(usuario: User) -> None:
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    enlace = f'{settings.FRONTEND_URL}/restablecer-contrasena/{uid}/{token}/'

    cuerpo_html = f"""
    <p>Hola {usuario.first_name},</p>
    <p>Recibimos una solicitud para restablecer tu contraseña en Lairn.</p>
    <p><a href="{enlace}">Haz clic aquí para elegir una nueva contraseña</a></p>
    <p>Si no fuiste tú, puedes ignorar este correo.</p>
    <p>Este enlace vence en unos días por seguridad.</p>
    """
    cuerpo_texto = (
        f'Hola {usuario.first_name},\n\n'
        'Recibimos una solicitud para restablecer tu contraseña en Lairn.\n'
        f'Abre este enlace para elegir una nueva: {enlace}\n\n'
        'Si no fuiste tú, puedes ignorar este correo.'
    )

    try:
        enviar_email(usuario.email, 'Restablece tu contraseña en Lairn', cuerpo_html, cuerpo_texto)
    except Exception:
        logger.exception('Fallo enviando correo de recuperación a %s', usuario.email)


def obtener_usuario_desde_uid(uid: str) -> User | None:
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
