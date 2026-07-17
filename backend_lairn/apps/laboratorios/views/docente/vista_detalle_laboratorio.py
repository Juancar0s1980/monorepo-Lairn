"""
Vista de detalle de un laboratorio, para el rol Docente.

Expone `/laboratorios/<laboratorio_id>/` con:
- GET: retorna el laboratorio con sus preguntas completas (incluidos los
  casos de test ocultos, útil para que el docente revise/edite).
- PATCH: edita título/instrucciones.
- DELETE: elimina el laboratorio (preguntas y casos de test caen en cascada).

El laboratorio se busca siempre vía `curso__docente=request.user`: si no
existe o pertenece a otro docente, la respuesta es 404.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.serializers import SerializadorLaboratorio, SerializadorLaboratorioDetalleDocente


@extend_schema_view(
    get=extend_schema(
        tags=['Laboratorios'],
        summary='Detalle de laboratorio (docente)',
        parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorLaboratorioDetalleDocente, 404: OpenApiResponse(description='Laboratorio no encontrado')},
    ),
    patch=extend_schema(
        tags=['Laboratorios'],
        summary='Editar laboratorio',
        request=SerializadorLaboratorio,
        parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorLaboratorio, 400: OpenApiResponse(description='Datos inválidos'), 404: OpenApiResponse(description='Laboratorio no encontrado')},
    ),
    delete=extend_schema(
        tags=['Laboratorios'],
        summary='Eliminar laboratorio',
        parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={204: OpenApiResponse(description='Laboratorio eliminado'), 404: OpenApiResponse(description='Laboratorio no encontrado')},
    ),
)
class VistaDetalleLaboratorio(APIView):
    permission_classes = [EsDocente]

    def _obtener(self, request, laboratorio_id):
        return Laboratorio.objects.get(id=laboratorio_id, curso__docente=request.user)

    def get(self, request, laboratorio_id):
        try:
            laboratorio = self._obtener(request, laboratorio_id)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorLaboratorioDetalleDocente(laboratorio)
        return Response(serializador.data)

    def patch(self, request, laboratorio_id):
        try:
            laboratorio = self._obtener(request, laboratorio_id)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorLaboratorio(laboratorio, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, laboratorio_id):
        try:
            laboratorio = self._obtener(request, laboratorio_id)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        laboratorio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
