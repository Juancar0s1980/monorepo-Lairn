"""
Vista colección de preguntas de código de un laboratorio, para el rol Docente.

Expone `/laboratorios/<laboratorio_id>/preguntas/` con GET (listado) y POST
(creación). El POST acepta `casos_test` anidados en el mismo payload — ver
`SerializadorPreguntaCodigoDocente` para el detalle de cómo se crean.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import Laboratorio, PreguntaCodigo
from apps.laboratorios.serializers import SerializadorPreguntaCodigoDocente


@extend_schema_view(
    get=extend_schema(
        tags=['Laboratorios'],
        summary='Listar preguntas de un laboratorio',
        parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorPreguntaCodigoDocente(many=True), 404: OpenApiResponse(description='Laboratorio no encontrado')},
    ),
    post=extend_schema(
        tags=['Laboratorios'],
        summary='Crear pregunta de código (con casos de test anidados)',
        request=SerializadorPreguntaCodigoDocente,
        parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={201: SerializadorPreguntaCodigoDocente, 400: OpenApiResponse(description='Datos inválidos'), 404: OpenApiResponse(description='Laboratorio no encontrado')},
    ),
)
class VistaPreguntasLaboratorio(APIView):
    permission_classes = [EsDocente]

    def get(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.get(id=laboratorio_id, curso__docente=request.user)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        preguntas = PreguntaCodigo.objects.filter(laboratorio=laboratorio)
        serializador = SerializadorPreguntaCodigoDocente(preguntas, many=True)
        return Response(serializador.data)

    def post(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.get(id=laboratorio_id, curso__docente=request.user)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorPreguntaCodigoDocente(data=request.data)
        if serializador.is_valid():
            serializador.save(laboratorio=laboratorio)
            return Response(serializador.data, status=status.HTTP_201_CREATED)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
