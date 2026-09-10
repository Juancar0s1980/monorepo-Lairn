from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.serializador_restablecer_contrasena import SerializadorRestablecerContrasena


@extend_schema(
    tags=['Usuarios'],
    summary='Restablecer contraseña',
    description='Establece una nueva contraseña usando el uid y token recibidos por correo.',
    request=SerializadorRestablecerContrasena,
    examples=[
        OpenApiExample(
            name='Restablecimiento',
            value={'uid': 'MQ', 'token': 'abc123-def456', 'password': 'NuevaClave1234*'},
            request_only=True,
        ),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaRestablecerContrasena',
            fields={'mensaje': drf_serializers.CharField()},
        ),
        400: OpenApiResponse(description='Enlace inválido/vencido o contraseña que no cumple los requisitos'),
    },
    auth=[],
)
class VistaRestablecerContrasena(APIView):
    permission_classes = [AllowAny]

    def post(self, peticion):
        serializador = SerializadorRestablecerContrasena(data=peticion.data)
        serializador.is_valid(raise_exception=True)
        serializador.save()
        return Response({'mensaje': 'Tu contraseña fue actualizada correctamente.'}, status=status.HTTP_200_OK)
