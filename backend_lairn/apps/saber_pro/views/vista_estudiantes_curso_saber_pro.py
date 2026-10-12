"""
Vista de gestión de estudiantes inscritos a un curso Saber Pro (HU-17.5 y
gestión de inscripciones).

Expone dos operaciones sobre el endpoint anidado al curso del docente:
- GET `/docente/cursos/<curso_id>/estudiantes/`: devuelve las inscripciones del
  curso del docente autenticado con el nombre completo del estudiante, su email
  y la fecha de ingreso (HU-17.5).
- DELETE `/docente/cursos/<curso_id>/estudiantes/<estudiante_id>/`: retira a un
  estudiante del curso eliminando su `InscripcionCursoSaberPro`. El borrado solo
  impacta la relación estudiante-curso: no elimina al usuario ni su historial, y
  el estudiante puede volver a unirse con un código vigente. Sigue el mismo
  patrón de `examenes` (`DELETE /cursos/<curso_id>/estudiantes/<estudiante_id>/`).

El curso se filtra por `docente=request.user`: si no existe o pertenece a otro
docente, la respuesta es 404 para no revelar la existencia de cursos ajenos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models import CursoSaberPro, InscripcionCursoSaberPro
from apps.saber_pro.serializers import SerializadorEstudianteInscrito


@extend_schema_view(
    get=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Estudiantes inscritos a un curso Saber Pro',
        description='Retorna la lista de estudiantes inscritos a un curso del docente autenticado, con su nombre, email y fecha de ingreso (HU-17.5).',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            200: SerializadorEstudianteInscrito(many=True),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Retirar estudiante de un curso Saber Pro',
        description=(
            'Elimina la inscripción de un estudiante del curso del docente autenticado. '
            'No elimina al usuario ni su historial, solo la relación con el curso; el '
            'estudiante puede volver a unirse con un código vigente.'
        ),
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
            OpenApiParameter('estudiante_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del estudiante a retirar'),
        ],
        responses={
            200: OpenApiResponse(description='Estudiante retirado del curso'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o estudiante no encontrado'),
        },
    ),
)
class VistaEstudiantesCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    # Lista las inscripciones del curso del docente con los datos del estudiante asociado.
    def get(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        inscripciones = InscripcionCursoSaberPro.objects.filter(curso=curso) \
            .select_related('estudiante')
        serializador = SerializadorEstudianteInscrito(inscripciones, many=True)
        return Response(serializador.data)

    # Retira a un estudiante del curso eliminando su inscripción (conserva usuario e historial).
    def delete(self, request, curso_id, estudiante_id):
        try:
            curso = CursoSaberPro.objects.get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        eliminadas, _ = InscripcionCursoSaberPro.objects.filter(
            curso=curso, estudiante_id=estudiante_id
        ).delete()

        if not eliminadas:
            return Response(
                {'detalle': 'Estudiante no encontrado en este curso.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {'detalle': 'Estudiante retirado del curso.'},
            status=status.HTTP_200_OK,
        )