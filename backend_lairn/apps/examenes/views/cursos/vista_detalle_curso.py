"""
Vista de detalle de un curso para el rol Docente.

Expone el endpoint `/cursos/<curso_id>/` con cuatro operaciones sobre un curso
específico:
- GET: retrieve.
- PUT: update completo.
- PATCH: update parcial.
- DELETE: eliminación (en cascada sobre inscripciones y exámenes asociados).

Todas las operaciones aplican el mismo filtro `docente=request.user` al
recuperar el curso, lo que combina en una sola query el chequeo de existencia
y el de propiedad: si el curso no existe *o* pertenece a otro docente, la
respuesta es 404. Esto evita una clase separada para validar ownership y no
filtra información sobre la existencia de cursos ajenos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.examenes.serializers import SerializadorCrearCurso


@extend_schema_view(
    get=extend_schema(
        tags=['Cursos'],
        summary='Obtener detalle de curso',
        description='Retorna la información detallada de un curso específico perteneciente al docente autenticado.',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            200: SerializadorCrearCurso,
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    put=extend_schema(
        tags=['Cursos'],
        summary='Actualizar curso',
        description='Actualiza la totalidad de los campos editables (nombre y descripcion) de un curso del docente autenticado.',
        request=SerializadorCrearCurso,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            200: SerializadorCrearCurso,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    patch=extend_schema(
        tags=['Cursos'],
        summary='Actualizar curso parcialmente',
        description='Actualiza uno o varios campos editables (nombre y descripcion) de un curso del docente autenticado.',
        request=SerializadorCrearCurso,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            200: SerializadorCrearCurso,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Cursos'],
        summary='Eliminar curso',
        description=(
            'Elimina un curso del docente autenticado. '
            'Esta operación elimina en cascada las inscripciones y exámenes asociados.'
        ),
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        ],
        responses={
            204: OpenApiResponse(description='Curso eliminado correctamente'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
)
class VistaDetalleCurso(APIView):
    permission_classes = [EsDocente]

    # Recupera el curso solicitado validando que pertenezca al docente autenticado.
    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearCurso(curso)
        return Response(serializador.data)

    # Actualiza la totalidad de los campos editables del curso del docente autenticado.
    def put(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearCurso(curso, data=request.data)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Actualiza parcialmente los campos editables del curso del docente autenticado.
    def patch(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearCurso(curso, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Elimina el curso del docente autenticado junto con sus dependencias en cascada.
    def delete(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        curso.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
