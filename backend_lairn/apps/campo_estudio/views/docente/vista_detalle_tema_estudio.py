"""
Vista de detalle de un tema de estudio, para el rol Docente.

Expone `/campo-estudio/temas/<tema_id>/` con PATCH (edición de
título/contenido antes o después de aprobar, curación de la IA) y DELETE
(rechaza un borrador pendiente o retira uno ya aprobado).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.campo_estudio.models import TemaEstudio
from apps.campo_estudio.serializers import SerializadorTemaEstudio


@extend_schema_view(
    patch=extend_schema(
        tags=['Campo de Estudio'],
        summary='Editar tema de estudio',
        request=SerializadorTemaEstudio,
        parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorTemaEstudio, 400: OpenApiResponse(description='Datos inválidos'), 404: OpenApiResponse(description='Tema no encontrado')},
    ),
    delete=extend_schema(
        tags=['Campo de Estudio'],
        summary='Eliminar tema de estudio',
        parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={204: OpenApiResponse(description='Tema eliminado'), 404: OpenApiResponse(description='Tema no encontrado')},
    ),
)
class VistaDetalleTemaEstudio(APIView):
    permission_classes = [EsDocente]

    def _obtener(self, request, tema_id):
        return TemaEstudio.objects.get(id=tema_id, curso__docente=request.user)

    def patch(self, request, tema_id):
        try:
            tema = self._obtener(request, tema_id)
        except TemaEstudio.DoesNotExist:
            return Response({'detalle': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorTemaEstudio(tema, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, tema_id):
        try:
            tema = self._obtener(request, tema_id)
        except TemaEstudio.DoesNotExist:
            return Response({'detalle': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        tema.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
