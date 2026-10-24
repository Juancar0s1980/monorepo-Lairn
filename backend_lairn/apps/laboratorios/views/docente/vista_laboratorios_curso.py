"""
Vista colección de laboratorios de un curso, para el rol Docente.

Expone `/cursos/<curso_id>/laboratorios/` con GET (listado) y POST (creación),
siguiendo el mismo patrón de ownership que `VistaObjetivosCurso`: el curso se
filtra por `docente=request.user`, así que un laboratorio ajeno o inexistente
responde 404 en vez de revelar su existencia.

El GET agrega actividad del grupo por laboratorio (`total_entregas` y
`promedio_puntaje`) para que la tarjeta de la lista no sea solo un título y
un conteo de preguntas — una sola consulta agregada para todos los
laboratorios del curso, no una por laboratorio (ver
`SerializadorLaboratorioListaDocente`).
"""

from django.db.models import Avg, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.laboratorios.models import Laboratorio, Entrega
from apps.laboratorios.serializers import SerializadorLaboratorio, SerializadorLaboratorioListaDocente


@extend_schema_view(
    get=extend_schema(
        tags=['Laboratorios'],
        summary='Listar laboratorios del curso',
        parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorLaboratorioListaDocente(many=True), 404: OpenApiResponse(description='Curso no encontrado')},
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

        stats = (
            Entrega.objects
            .filter(pregunta__laboratorio__in=laboratorios)
            .values('pregunta__laboratorio_id')
            .annotate(total=Count('id'), promedio=Avg('puntaje'))
        )
        stats_por_lab = {fila['pregunta__laboratorio_id']: fila for fila in stats}

        serializador = SerializadorLaboratorioListaDocente(
            laboratorios, many=True, context={'stats_por_lab': stats_por_lab}
        )
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
