from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.users.serializers.serializador_usuario import SerializadorUsuario


@extend_schema(
    tags=['Usuarios'],
    summary='Mis datos',
    description='Retorna los datos del usuario autenticado.',
    responses={
        200: SerializadorUsuario,
        401: OpenApiResponse(description='Token inválido o no enviado'),
    },
)
class VistaMisDatos(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, peticion):
        serializador = SerializadorUsuario(peticion.user)
        return Response(serializador.data)
