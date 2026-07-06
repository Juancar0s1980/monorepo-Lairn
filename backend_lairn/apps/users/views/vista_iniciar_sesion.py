from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from apps.users.serializers.serializador_iniciar_sesion import SerializadorIniciarSesion


@extend_schema(
    tags=['Usuarios'],
    summary='Iniciar sesión',
    description='Autentica al usuario con correo y contraseña. Retorna access y refresh token.',
    request=SerializadorIniciarSesion,
    examples=[
        OpenApiExample(
            name='Docente de prueba',
            value={'email': 'docente@pseudotutor.com', 'password': 'Docente1234*'},
            request_only=True,
        ),
        OpenApiExample(
            name='Estudiante de prueba',
            value={'email': 'estudiante@pseudotutor.com', 'password': 'Estudiante1234*'},
            request_only=True,
        ),
        OpenApiExample(
            name='Administrador de prueba',
            value={'email': 'admin@pseudotutor.com', 'password': 'admin1234'},
            request_only=True,
        ),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaIniciarSesion',
            fields={
                'access': drf_serializers.CharField(),
                'refresh': drf_serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description='Credenciales incorrectas'),
    },
    auth=[],
)
class VistaIniciarSesion(APIView):
    permission_classes = [AllowAny]

    def post(self, peticion):
        serializador = SerializadorIniciarSesion(data=peticion.data)
        serializador.is_valid(raise_exception=True)
        return Response(serializador.validated_data, status=status.HTTP_200_OK)
