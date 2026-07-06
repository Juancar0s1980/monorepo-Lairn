"""
Vista de detalle de un usuario para el rol Administrador.

Expone el endpoint `/administracion/usuarios/<usuario_id>/` con:
- PATCH: reasigna el rol (`role_id`) y/o activa-desactiva (`is_active`) al usuario.
- DELETE: elimina la cuenta del usuario.

Ambas operaciones bloquean que el administrador se modifique o elimine a sí
mismo, para evitar que quede sin rol de administrador o sin acceso al panel
por error.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsAdministrador
from apps.users.models.user import User
from apps.users.serializers.serializador_gestion_usuario import SerializadorGestionUsuario


@extend_schema_view(
    patch=extend_schema(
        tags=['Usuarios'],
        summary='Actualizar rol o estado de un usuario',
        description='Reasigna el rol (`role_id`) y/o activa-desactiva (`is_active`) a un usuario. No permite modificarse a sí mismo.',
        request=SerializadorGestionUsuario,
        parameters=[
            OpenApiParameter('usuario_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del usuario'),
        ],
        responses={
            200: SerializadorGestionUsuario,
            400: OpenApiResponse(description='Datos inválidos o intento de auto-modificación'),
            403: OpenApiResponse(description='Solo el administrador puede acceder'),
            404: OpenApiResponse(description='Usuario no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Usuarios'],
        summary='Eliminar usuario',
        description='Elimina la cuenta de un usuario. No permite eliminarse a sí mismo.',
        parameters=[
            OpenApiParameter('usuario_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del usuario'),
        ],
        responses={
            204: OpenApiResponse(description='Usuario eliminado correctamente'),
            400: OpenApiResponse(description='Intento de auto-eliminación'),
            403: OpenApiResponse(description='Solo el administrador puede acceder'),
            404: OpenApiResponse(description='Usuario no encontrado'),
        },
    ),
)
class VistaDetalleUsuarioAdmin(APIView):
    permission_classes = [EsAdministrador]

    # Actualiza parcialmente el rol y/o el estado activo de un usuario, salvo el propio.
    def patch(self, request, usuario_id):
        if usuario_id == request.user.id:
            return Response(
                {'detalle': 'No puedes modificar tu propia cuenta desde este panel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return Response({'detalle': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorGestionUsuario(usuario, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Elimina la cuenta de un usuario, salvo la propia.
    def delete(self, request, usuario_id):
        if usuario_id == request.user.id:
            return Response(
                {'detalle': 'No puedes eliminar tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return Response({'detalle': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
