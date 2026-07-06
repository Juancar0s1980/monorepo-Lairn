"""
Vista de gestión de estudiantes inscritos a un curso, para el rol Docente.

Expone dos operaciones sobre el endpoint anidado al curso:
- GET `/cursos/<curso_id>/estudiantes/`: lista los estudiantes inscritos junto
  con su nombre, email y fecha de inscripción.
- DELETE `/cursos/<curso_id>/estudiantes/<estudiante_id>/`: elimina la
  inscripción de un estudiante específico.

Aunque la URL y el nombre hablan de "estudiantes", el recurso que efectivamente
se manipula es `Inscripcion`. El DELETE no borra al usuario ni su historial,
solo elimina la relación con el curso. Cada operación filtra el curso por
`docente=request.user` para garantizar que el docente solo opere sobre cursos
propios; si el curso no existe o pertenece a otro docente, la respuesta es 404
en lugar de 403 para no revelar la existencia de cursos ajenos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, Inscripcion
from apps.examenes.serializers import SerializadorEstudianteCurso


@extend_schema_view(
    get=extend_schema(
        tags=['Cursos'],
        summary='Listar estudiantes del curso',
        description='Retorna la lista de estudiantes inscritos en el curso con su nombre, email y fecha de inscripción.',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            200: SerializadorEstudianteCurso(many=True),
            403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Cursos'],
        summary='Eliminar estudiante del curso',
        description=(
            'Elimina la inscripción de un estudiante del curso. '
            'No elimina los resultados ni el historial del estudiante, solo la inscripción.'
        ),
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
            OpenApiParameter('estudiante_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del estudiante a eliminar'),
        ],
        responses={
            200: OpenApiResponse(description='Estudiante eliminado del curso'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o estudiante no encontrado'),
        },
    ),
)
class VistaEstudiantesCurso(APIView):
    permission_classes = [EsDocente]

    # Lista las inscripciones del curso del docente autenticado con los datos del estudiante asociado.
    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        inscripciones = Inscripcion.objects.filter(curso=curso).select_related('estudiante')
        serializador = SerializadorEstudianteCurso(inscripciones, many=True)
        return Response(serializador.data)

    # Elimina la inscripción de un estudiante específico en un curso del docente autenticado.
    def delete(self, request, curso_id, estudiante_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        eliminados, _ = Inscripcion.objects.filter(
            curso=curso, estudiante_id=estudiante_id
        ).delete()

        if not eliminados:
            return Response({'detalle': 'Estudiante no encontrado en este curso.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'detalle': 'Estudiante eliminado del curso.'}, status=status.HTTP_200_OK)
