"""
Inicio de sesión con la cuenta Google institucional (HU-26).

Reglas (todas en el servidor; no se confía en nada que diga el navegador):
1. El ID token de Google se verifica con Google: firma, audiencia = GOOGLE_CLIENT_ID, emisor y vencimiento.
2. Correo verificado, dominio de Google Workspace (`hd`) y correo dentro de DOMINIOS_INSTITUCIONALES.
3. La cuenta debe existir en PseudoTutor (la crea TI, la importación o el Administrador): no hay autoregistro.
4. La cuenta debe estar activa. Al desactivarla, simplejwt también rechaza sus tokens vigentes.
5. El `sub` de Google se vincula en el primer ingreso; un `sub` distinto para el mismo correo se rechaza.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import IdentidadGoogle

logger = logging.getLogger(__name__)
EMISORES = {'accounts.google.com', 'https://accounts.google.com'}


class ErrorAcceso(Exception):
    """Ingreso rechazado: `mensaje` es para el usuario, `codigo` para el frontend y el registro."""

    def __init__(self, mensaje, codigo, estado=403):
        super().__init__(mensaje)
        self.mensaje, self.codigo, self.estado = mensaje, codigo, estado


def emitir_tokens(usuario) -> dict:
    """JWT con el claim `rol`, igual que el inicio de sesión con contraseña."""
    refresco = RefreshToken.for_user(usuario)
    rol = usuario.role.name if usuario.role else None
    refresco['rol'] = rol
    refresco.access_token['rol'] = rol
    return {'access': str(refresco.access_token), 'refresh': str(refresco)}


def verificar_token_google(credencial: str) -> dict:
    """Verifica el ID token con las llaves públicas de Google. Aislado para simularlo en pruebas."""
    from google.auth.transport import requests as transporte
    from google.oauth2 import id_token

    return id_token.verify_oauth2_token(credencial, transporte.Request(), settings.GOOGLE_CLIENT_ID,
                                        clock_skew_in_seconds=10)


def correo_institucional(correo: str) -> bool:
    dominio = correo.rsplit('@', 1)[-1].lower() if '@' in correo else ''
    return dominio in settings.DOMINIOS_INSTITUCIONALES


def autenticar_con_google(credencial: str):
    """Retorna el usuario autenticado o lanza ErrorAcceso."""
    if not settings.GOOGLE_CLIENT_ID:
        raise ErrorAcceso('El inicio de sesión con Google no está configurado. Contacta a soporte.', 'sin_configurar', 503)
    if not credencial or not isinstance(credencial, str):
        raise ErrorAcceso('No se recibió la credencial de Google.', 'sin_credencial', 400)
    try:
        datos = verificar_token_google(credencial)
    except ValueError:
        logger.warning('Ingreso con Google rechazado: token inválido o vencido')
        raise ErrorAcceso('No se pudo validar tu cuenta de Google. Vuelve a intentarlo.', 'token_invalido', 401)
    if datos.get('iss') not in EMISORES:
        raise ErrorAcceso('No se pudo validar tu cuenta de Google. Vuelve a intentarlo.', 'token_invalido', 401)

    correo = str(datos.get('email') or '').strip().lower()
    if not datos.get('email_verified'):
        raise ErrorAcceso('Tu correo de Google no está verificado.', 'correo_no_verificado')
    dominio_ws = str(datos.get('hd') or '').lower()
    if not correo_institucional(correo) or dominio_ws not in settings.DOMINIOS_INSTITUCIONALES:
        logger.warning('Ingreso con Google rechazado: correo no institucional (%s)', correo.rsplit('@', 1)[-1])
        dominios = ', '.join('@' + d for d in settings.DOMINIOS_INSTITUCIONALES)
        raise ErrorAcceso(f'Usa tu correo institucional ({dominios}).', 'no_institucional')

    usuario = get_user_model().objects.select_related('role').filter(email__iexact=correo).first()
    if usuario is None:
        logger.warning('Ingreso con Google rechazado: cuenta no habilitada')
        raise ErrorAcceso('Tu correo institucional no está habilitado en PseudoTutor. Solicita el acceso a TI.', 'sin_cuenta')
    if not usuario.is_active:
        logger.warning('Ingreso con Google rechazado: cuenta desactivada (usuario %s)', usuario.pk)
        raise ErrorAcceso('Tu cuenta está desactivada. Comunícate con TI.', 'cuenta_inactiva')

    sub = str(datos.get('sub') or '')
    if not sub:
        raise ErrorAcceso('No se pudo validar tu cuenta de Google. Vuelve a intentarlo.', 'token_invalido', 401)
    try:
        with transaction.atomic():
            identidad, creada = IdentidadGoogle.objects.get_or_create(usuario=usuario, defaults={'sub': sub, 'dominio': dominio_ws})
    except IntegrityError:
        # Ese `sub` ya pertenece a otra cuenta de PseudoTutor.
        raise ErrorAcceso('Esta cuenta de Google ya está vinculada a otro usuario. Comunícate con TI.', 'identidad_en_uso')
    if not creada and identidad.sub != sub:
        logger.warning('Ingreso con Google rechazado: identidad distinta para el usuario %s', usuario.pk)
        raise ErrorAcceso('El correo pertenece a otra identidad de Google. Comunícate con TI.', 'identidad_distinta')
    identidad.ultimo_ingreso = timezone.now()
    identidad.save(update_fields=['ultimo_ingreso'])
    usuario.last_login = identidad.ultimo_ingreso
    usuario.save(update_fields=['last_login'])
    return usuario
