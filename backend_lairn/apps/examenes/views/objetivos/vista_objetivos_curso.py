"""
Vista colección de objetivos de aprendizaje de un curso, para el rol Docente.

Expone `/cursos/<curso_id>/objetivos/` con:
- GET: lista los objetivos del curso (ordenados por `orden`).
- POST: crea un objetivo (escrito a mano o una sugerencia de IA aceptada).

Ambas operaciones filtran el curso por `docente=request.user`: si el curso no
existe o pertenece a otro docente la respuesta es 404, siguiendo el mismo
patrón de ownership del resto de vistas de la app.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, ObjetivoCurso
from apps.examenes.serializers import SerializadorObjetivo


@extend_schema_view(
    get=extend_schema(
        tags=['Objetivos'],
        summary='Listar objetivos del curso',
        description='Retorna los objetivos de aprendizaje del curso del docente autenticado.',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            200: SerializadorObjetivo(many=True),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    post=extend_schema(
        tags=['Objetivos'],
        summary='Crear objetivo',
        description='Agrega un objetivo de aprendizaje al curso (manual o sugerencia de IA aceptada).',
        request=SerializadorObjetivo,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            201: SerializadorObjetivo,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
)
class VistaObjetivosCurso(APIView):
    permission_classes = [EsDocente]

    # Lista los objetivos del curso del docente autenticado.
    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        objetivos = ObjetivoCurso.objects.filter(curso=curso)
        serializador = SerializadorObjetivo(objetivos, many=True)
        return Response(serializador.data)

    # Crea un objetivo en el curso del docente autenticado.
    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorObjetivo(data=request.data)
        if serializador.is_valid():
            serializador.save(curso=curso)
            return Response(serializador.data, status=status.HTTP_201_CREATED)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
