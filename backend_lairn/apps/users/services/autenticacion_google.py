"""
Ingreso y alta de cuentas con la cuenta Google institucional (HU-26).

Reglas (todas en el servidor; no se confía en nada que diga el navegador):
1. El ID token de Google se verifica con Google: firma, audiencia = GOOGLE_CLIENT_ID, emisor y vencimiento.
2. Correo verificado, dominio de Google Workspace (`hd`) y correo dentro de DOMINIOS_INSTITUCIONALES.
3. Si la cuenta no existe se crea según el acceso usado:
   - Acceso de estudiantes: rol Estudiante, activa.
   - Acceso de personal: la persona elige su rol. Docente queda activa; Administrador, Coordinador y
     Vicerrector quedan inactivas hasta que un Administrador apruebe la solicitud (SolicitudCuenta).
   - Los correos de ADMINISTRADORES_INICIALES quedan como Administrador activo (cuenta predeterminada).
4. La cuenta debe estar activa. Al desactivarla (por ejemplo, fin de contrato), simplejwt también
   rechaza sus tokens vigentes.
5. El `sub` de Google se vincula al crear o en el primer ingreso; un `sub` distinto se rechaza.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import IdentidadGoogle, OpcionesEstadoCuenta, Role, SolicitudCuenta

logger = logging.getLogger(__name__)
EMISORES = {'accounts.google.com', 'https://accounts.google.com'}

PORTAL_ESTUDIANTES = 'estudiantes'
PORTAL_PERSONAL = 'personal'
ROL_ESTUDIANTE = 'Estudiante'
ROL_DOCENTE = 'Docente'
ROL_ADMINISTRADOR = 'Administrador'
# Roles que se pueden pedir en el acceso de personal y si requieren aprobación del Administrador.
ROLES_PERSONAL = {'Docente': False, 'Coordinador': True, 'Vicerrector': True, 'Administrador': True}


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


def _dividir(texto: str) -> tuple[str, str]:
    partes = (texto or '').split()
    return (partes[0] if partes else '')[:50], ' '.join(partes[1:])[:50]


def _nombres(datos: dict, correo: str) -> dict:
    """Nombres y apellidos desde el perfil de Google (given_name / family_name)."""
    primer_nombre, segundo_nombre = _dividir(datos.get('given_name', ''))
    primer_apellido, segundo_apellido = _dividir(datos.get('family_name', ''))
    if not primer_nombre:
        primer_nombre = correo.split('@', 1)[0].split('.', 1)[0].capitalize()[:50]
    return {'first_name': primer_nombre, 'second_name': segundo_nombre,
            'first_last_name': primer_apellido or '-', 'second_last_name': segundo_apellido}


def _validar_token(credencial) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise ErrorAcceso('El inicio de sesión con Google no está configurado. Contacta a soporte.', 'sin_configurar', 503)
    if not credencial or not isinstance(credencial, str):
        raise ErrorAcceso('No se recibió la credencial de Google.', 'sin_credencial', 400)
    try:
        datos = verificar_token_google(credencial)
    except ValueError:
        logger.warning('Ingreso con Google rechazado: token inválido o vencido')
        raise ErrorAcceso('No se pudo validar tu cuenta de Google. Vuelve a intentarlo.', 'token_invalido', 401)
    if datos.get('iss') not in EMISORES or not str(datos.get('sub') or ''):
        raise ErrorAcceso('No se pudo validar tu cuenta de Google. Vuelve a intentarlo.', 'token_invalido', 401)
    if not datos.get('email_verified'):
        raise ErrorAcceso('Tu correo de Google no está verificado.', 'correo_no_verificado')
    correo = str(datos.get('email') or '').strip().lower()
    dominio_ws = str(datos.get('hd') or '').lower()
    if not correo_institucional(correo) or dominio_ws not in settings.DOMINIOS_INSTITUCIONALES:
        logger.warning('Ingreso con Google rechazado: correo no institucional (%s)', correo.rsplit('@', 1)[-1])
        dominios = ', '.join('@' + d for d in settings.DOMINIOS_INSTITUCIONALES)
        raise ErrorAcceso(f'Solo se aceptan correos institucionales ({dominios}).', 'no_institucional')
    return {**datos, 'email': correo, 'hd': dominio_ws}


def _crear_cuenta(datos: dict, portal: str, rol_pedido: str | None):
    """Crea la cuenta del primer ingreso. Retorna (usuario, requiere_aprobacion)."""
    correo = datos['email']
    if correo in settings.ADMINISTRADORES_INICIALES:
        nombre_rol, requiere_aprobacion = ROL_ADMINISTRADOR, False
    elif portal == PORTAL_PERSONAL:
        if rol_pedido not in ROLES_PERSONAL:
            raise ErrorAcceso('Elige tu rol antes de continuar con Google.', 'rol_requerido', 400)
        nombre_rol, requiere_aprobacion = rol_pedido, ROLES_PERSONAL[rol_pedido]
    else:
        nombre_rol, requiere_aprobacion = ROL_ESTUDIANTE, False

    rol = Role.objects.filter(name=nombre_rol).first()
    if rol is None:
        raise ErrorAcceso('El rol elegido no está configurado. Contacta a soporte.', 'rol_inexistente', 503)
    try:
        with transaction.atomic():
            usuario = get_user_model().objects.create_user(
                email=correo, password=None, is_active=not requiere_aprobacion,
                role=None if requiere_aprobacion else rol, **_nombres(datos, correo))
            IdentidadGoogle.objects.create(usuario=usuario, sub=str(datos['sub']), dominio=datos['hd'])
            if requiere_aprobacion:
                SolicitudCuenta.objects.create(usuario=usuario, rol_solicitado=rol)
    except IntegrityError:
        raise ErrorAcceso('Esta cuenta de Google ya está vinculada a otro usuario. Comunícate con TI.', 'identidad_en_uso')
    logger.info('Cuenta creada con Google: usuario %s, rol %s, pendiente=%s', usuario.pk, nombre_rol, requiere_aprobacion)
    return usuario, requiere_aprobacion


def _rechazar_inactiva(usuario):
    solicitud = SolicitudCuenta.objects.select_related('rol_solicitado').filter(usuario=usuario).first()
    if solicitud and solicitud.estado == OpcionesEstadoCuenta.PENDIENTE:
        raise ErrorAcceso(f'Tu cuenta de {solicitud.rol_solicitado.name} está pendiente de aprobación del Administrador. '
                          'Podrás entrar cuando la apruebe.', 'cuenta_pendiente')
    if solicitud and solicitud.estado == OpcionesEstadoCuenta.RECHAZADA:
        motivo = f' Motivo: {solicitud.motivo}' if solicitud.motivo else ''
        raise ErrorAcceso(f'Tu solicitud de cuenta de {solicitud.rol_solicitado.name} fue rechazada.{motivo}', 'solicitud_rechazada')
    logger.warning('Ingreso con Google rechazado: cuenta desactivada (usuario %s)', usuario.pk)
    raise ErrorAcceso('Tu cuenta está desactivada. Comunícate con TI.', 'cuenta_inactiva')


def autenticar_con_google(credencial: str, portal: str = PORTAL_ESTUDIANTES, rol: str | None = None):
    """Retorna el usuario autenticado o lanza ErrorAcceso (también cuando la cuenta queda pendiente)."""
    datos = _validar_token(credencial)
    sub = str(datos['sub'])
    usuario = get_user_model().objects.select_related('role').filter(email__iexact=datos['email']).first()

    if usuario is None:
        usuario, requiere_aprobacion = _crear_cuenta(datos, portal, rol)
        if requiere_aprobacion:
            raise ErrorAcceso(f'Solicitud enviada: tu cuenta de {rol} quedará activa cuando el Administrador la apruebe.',
                              'solicitud_enviada', 202)
        identidad = usuario.identidad_google
    else:
        if datos['email'] in settings.ADMINISTRADORES_INICIALES and (
                not usuario.is_active or not usuario.role or usuario.role.name != ROL_ADMINISTRADOR):
            # Cuenta predeterminada: siempre entra como Administrador activo, aunque ya existiera con otro rol.
            usuario.role = Role.objects.get(name=ROL_ADMINISTRADOR)
            usuario.is_active = True
            usuario.save(update_fields=['role', 'is_active'])
            SolicitudCuenta.objects.filter(usuario=usuario, estado=OpcionesEstadoCuenta.PENDIENTE).delete()
        if not usuario.is_active:
            _rechazar_inactiva(usuario)
        try:
            with transaction.atomic():
                identidad, creada = IdentidadGoogle.objects.get_or_create(usuario=usuario, defaults={'sub': sub, 'dominio': datos['hd']})
        except IntegrityError:
            raise ErrorAcceso('Esta cuenta de Google ya está vinculada a otro usuario. Comunícate con TI.', 'identidad_en_uso')
        if not creada and identidad.sub != sub:
            logger.warning('Ingreso con Google rechazado: identidad distinta para el usuario %s', usuario.pk)
            raise ErrorAcceso('El correo pertenece a otra identidad de Google. Comunícate con TI.', 'identidad_distinta')

    identidad.ultimo_ingreso = timezone.now()
    identidad.save(update_fields=['ultimo_ingreso'])
    usuario.last_login = identidad.ultimo_ingreso
    usuario.save(update_fields=['last_login'])
    return usuario
