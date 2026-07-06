"""
Vista de solo lectura de los roles del sistema, para el rol Administrador.

Expone el endpoint `/roles/` que lista los roles existentes (Administrador,
Docente, Estudiante), usados por el panel de administración para poblar el
selector de reasignación de rol de un usuario.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.users.models.role import Role
from apps.users.serializers.serializador_rol import SerializadorRol


@extend_schema(
    tags=['Usuarios'],
    summary='Listar roles',
    description='Retorna los roles existentes en el sistema. Solo accesible para el Administrador.',
    responses={
        200: SerializadorRol(many=True),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaListaRoles(APIView):
    permission_classes = [EsAdministrador]

    # Lista todos los roles existentes en el sistema.
    def get(self, request):
        roles = Role.objects.all().order_by('name')
        serializador = SerializadorRol(roles, many=True)
        return Response(serializador.data)
