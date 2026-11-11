"""Revisiones de arranque del acceso institucional (HU-26)."""

from django.conf import settings
from django.core.checks import Warning, register


@register()
def acceso_institucional_configurado(app_configs, **kwargs):
    # Con el acceso solo institucional y sin GOOGLE_CLIENT_ID nadie podría iniciar sesión.
    if getattr(settings, 'AUTENTICACION_SOLO_INSTITUCIONAL', False) and not getattr(settings, 'GOOGLE_CLIENT_ID', ''):
        return [Warning(
            'AUTENTICACION_SOLO_INSTITUCIONAL está activo pero GOOGLE_CLIENT_ID está vacío: nadie podrá iniciar sesión.',
            hint='Configura GOOGLE_CLIENT_ID en .env o usa AUTENTICACION_SOLO_INSTITUCIONAL=False en desarrollo.',
            id='users.W001',
        )]
    return []
