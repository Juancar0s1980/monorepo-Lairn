from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers


@extend_schema(
    tags=['Usuarios'],
    summary='Cerrar sesión',
    description='Invalida el refresh token. El access token expira solo después de 5 minutos.',
    request=inline_serializer(
        name='PeticionCerrarSesion',
        fields={
            'refresh': drf_serializers.CharField(),
        }
    ),
    examples=[
        OpenApiExample(
            name='Cerrar sesion',
            value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'},
            request_only=True,
        ),
    ],
    responses={
        204: OpenApiResponse(description='Sesión cerrada correctamente'),
        400: OpenApiResponse(description='Token inválido o ya expirado'),
        401: OpenApiResponse(description='No autenticado'),
    },
)
class VistaCerrarSesion(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, peticion):
        try:
            token_refresco = peticion.data.get('refresh')
            token = RefreshToken(token_refresco)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError:
            return Response({'error': 'Token inválido o ya expirado.'}, status=status.HTTP_400_BAD_REQUEST)
