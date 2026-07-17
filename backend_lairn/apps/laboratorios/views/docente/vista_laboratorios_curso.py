"""
Vista colección de laboratorios de un curso, para el rol Docente.

Expone `/cursos/<curso_id>/laboratorios/` con GET (listado) y POST (creación),
siguiendo el mismo patrón de ownership que `VistaObjetivosCurso`: el curso se
filtra por `docente=request.user`, así que un laboratorio ajeno o inexistente
responde 404 en vez de revelar su existencia.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.serializers import SerializadorLaboratorio


@extend_schema_view(
    get=extend_schema(
        tags=['Laboratorios'],
        summary='Listar laboratorios del curso',
        parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorLaboratorio(many=True), 404: OpenApiResponse(description='Curso no encontrado')},
    ),
    post=extend_schema(
        tags=['Laboratorios'],
        summary='Crear laboratorio',
        request=SerializadorLaboratorio,
        parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={201: SerializadorLaboratorio, 400: OpenApiResponse(description='Datos inválidos'), 404: OpenApiResponse(description='Curso no encontrado')},
    ),
)
class VistaLaboratoriosCurso(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        laboratorios = Laboratorio.objects.filter(curso=curso)
        serializador = SerializadorLaboratorio(laboratorios, many=True)
        return Response(serializador.data)

    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorLaboratorio(data=request.data)
        if serializador.is_valid():
            serializador.save(curso=curso)
            return Response(serializador.data, status=status.HTTP_201_CREATED)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
