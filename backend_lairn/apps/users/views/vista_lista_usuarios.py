"""
Vista colección de usuarios para el rol Administrador.

Expone el endpoint `/administracion/usuarios/` con:
- GET: lista todos los usuarios del sistema con su rol asignado.

Se restringe a una sola operación de colección porque el alta de usuarios ya
existe vía `/registrar/` y no necesita duplicarse aquí; esta vista es de solo
lectura para el panel de administración.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.users.models.user import User
from apps.users.serializers.serializador_gestion_usuario import SerializadorGestionUsuario


@extend_schema(
    tags=['Usuarios'],
    summary='Listar usuarios',
    description='Retorna todos los usuarios del sistema con su rol asignado. Solo accesible para el Administrador.',
    responses={
        200: SerializadorGestionUsuario(many=True),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaListaUsuarios(APIView):
    permission_classes = [EsAdministrador]

    # Lista todos los usuarios del sistema junto con su rol.
    def get(self, request):
        usuarios = User.objects.select_related('role').all().order_by('email')
        serializador = SerializadorGestionUsuario(usuarios, many=True)
        return Response(serializador.data)
