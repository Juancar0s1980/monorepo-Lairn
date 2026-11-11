"""
Acceso institucional con Google (HU-26).

- `GET  usuarios/config-acceso/`            público: si el acceso es solo institucional, client_id y dominios
- `POST usuarios/iniciar-sesion-google/`    {credential: ID token de Google} → {access, refresh}
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.users.services.autenticacion_google import ErrorAcceso, autenticar_con_google, emitir_tokens

MENSAJE_SOLO_INSTITUCIONAL = 'El acceso es solo con tu cuenta Google institucional.'


def solo_institucional() -> bool:
    return bool(settings.AUTENTICACION_SOLO_INSTITUCIONAL)


class VistaConfigAcceso(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(tags=['Usuarios'], summary='Configuración del inicio de sesión', auth=[])
    def get(self, request):
        return Response({
            'solo_institucional': solo_institucional(),
            'google_client_id': settings.GOOGLE_CLIENT_ID,
            'dominios': settings.DOMINIOS_INSTITUCIONALES,
        })


class VistaIniciarSesionGoogle(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'acceso'

    @extend_schema(tags=['Usuarios'], summary='Iniciar sesión con Google institucional', auth=[])
    def post(self, request):
        try:
            usuario = autenticar_con_google(request.data.get('credential'))
        except ErrorAcceso as exc:
            return Response({'detalle': exc.mensaje, 'codigo': exc.codigo}, status=exc.estado)
        return Response(emitir_tokens(usuario))
