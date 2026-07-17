"""
Vista de detalle de una pregunta de código, para el rol Docente.

Expone `/laboratorios/preguntas/<pregunta_id>/` con PATCH (edición, incluidos
los casos de test anidados — se reemplazan enteros si vienen en el payload)
y DELETE.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import PreguntaCodigo
from apps.laboratorios.serializers import SerializadorPreguntaCodigoDocente


@extend_schema_view(
    patch=extend_schema(
        tags=['Laboratorios'],
        summary='Editar pregunta de código',
        request=SerializadorPreguntaCodigoDocente,
        parameters=[OpenApiParameter('pregunta_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorPreguntaCodigoDocente, 400: OpenApiResponse(description='Datos inválidos'), 404: OpenApiResponse(description='Pregunta no encontrada')},
    ),
    delete=extend_schema(
        tags=['Laboratorios'],
        summary='Eliminar pregunta de código',
        parameters=[OpenApiParameter('pregunta_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={204: OpenApiResponse(description='Pregunta eliminada'), 404: OpenApiResponse(description='Pregunta no encontrada')},
    ),
)
class VistaDetallePreguntaCodigo(APIView):
    permission_classes = [EsDocente]

    def _obtener(self, request, pregunta_id):
        return PreguntaCodigo.objects.get(id=pregunta_id, laboratorio__curso__docente=request.user)

    def patch(self, request, pregunta_id):
        try:
            pregunta = self._obtener(request, pregunta_id)
        except PreguntaCodigo.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorPreguntaCodigoDocente(pregunta, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pregunta_id):
        try:
            pregunta = self._obtener(request, pregunta_id)
        except PreguntaCodigo.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        pregunta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
