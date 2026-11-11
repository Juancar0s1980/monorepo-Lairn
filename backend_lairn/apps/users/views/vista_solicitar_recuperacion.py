from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.views.vista_acceso_google import MENSAJE_SOLO_INSTITUCIONAL, solo_institucional
from rest_framework.views import APIView

from apps.users.models.user import User
from apps.users.serializers.serializador_solicitar_recuperacion import SerializadorSolicitarRecuperacion
from apps.users.services.recuperacion_contrasena import enviar_correo_recuperacion


@extend_schema(
    tags=['Usuarios'],
    summary='Solicitar recuperación de contraseña',
    description=(
        'Envía un correo con un enlace para restablecer la contraseña. '
        'Siempre responde 200 con el mismo mensaje exista o no ese correo, '
        'para no revelar qué correos están registrados.'
    ),
    request=SerializadorSolicitarRecuperacion,
    examples=[
        OpenApiExample(
            name='Solicitud',
            value={'email': 'estudiante@pseudotutor.com'},
            request_only=True,
        ),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaSolicitarRecuperacion',
            fields={'mensaje': drf_serializers.CharField()},
        ),
        400: OpenApiResponse(description='Correo inválido'),
    },
    auth=[],
)
class VistaSolicitarRecuperacion(APIView):
    permission_classes = [AllowAny]

    MENSAJE = 'Si ese correo está registrado, te enviamos un enlace para restablecer tu contraseña.'

    def post(self, peticion):
        if solo_institucional():
            return Response({'detalle': MENSAJE_SOLO_INSTITUCIONAL, 'codigo': 'solo_institucional'}, status=403)
        serializador = SerializadorSolicitarRecuperacion(data=peticion.data)
        serializador.is_valid(raise_exception=True)

        usuario = User.objects.filter(email__iexact=serializador.validated_data['email']).first()
        if usuario is not None:
            enviar_correo_recuperacion(usuario)

        return Response({'mensaje': self.MENSAJE}, status=status.HTTP_200_OK)
