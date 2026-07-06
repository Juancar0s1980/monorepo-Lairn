from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from apps.users.serializers.serializador_registrar import SerializadorRegistrar


@extend_schema(
    tags=['Usuarios'],
    summary='Registrarse',
    description='Crea una cuenta nueva. El rol Estudiante se asigna automáticamente.',
    request=SerializadorRegistrar,
    examples=[
        OpenApiExample(
            name='Estudiante nuevo',
            value={
                'first_name': 'Ana',
                'second_name': 'Maria',
                'first_last_name': 'Garcia',
                'second_last_name': 'Lopez',
                'email': 'ana.garcia@correo.com',
                'password': 'contrasena123',
            },
            request_only=True,
        ),
    ],
    responses={
        201: inline_serializer(
            name='RespuestaRegistrar',
            fields={
                'access': drf_serializers.CharField(),
                'refresh': drf_serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description='Datos inválidos o correo ya registrado'),
    },
    auth=[],
)
class VistaRegistrar(APIView):
    permission_classes = [AllowAny]

    def post(self, peticion):
        serializador = SerializadorRegistrar(data=peticion.data)
        serializador.is_valid(raise_exception=True)
        usuario = serializador.save()
        token_refresco = RefreshToken.for_user(usuario)
        return Response({
            'access': str(token_refresco.access_token),
            'refresh': str(token_refresco),
        }, status=status.HTTP_201_CREATED)
