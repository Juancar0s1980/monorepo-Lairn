"""
Vista de listado de temas de estudio de un curso, para el rol Estudiante.

Expone `GET /mis-cursos/<curso_id>/campo-estudio/temas/`. Requiere una
inscripción activa (igual que `VistaLaboratoriosCursoEstudiante`) y que el
docente haya activado `campo_estudio_habilitado` en el curso; solo se listan
temas `estado='aprobado'`.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Inscripcion
from apps.campo_estudio.models import TemaEstudio
from apps.campo_estudio.serializers import SerializadorTemaEstudio


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Temas de estudio de un curso (estudiante)',
    description=(
        'Retorna los temas de estudio aprobados del curso. Requiere estar '
        'inscrito y que el docente haya activado el Campo de Estudio.'
    ),
    responses={
        200: SerializadorTemaEstudio(many=True),
        403: OpenApiResponse(description='No estás inscrito o el Campo de Estudio está desactivado'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaTemasEstudioEstudiante(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        if not curso.campo_estudio_habilitado:
            return Response({'detalle': 'El Campo de Estudio no está activado para este curso.'}, status=status.HTTP_403_FORBIDDEN)

        temas = TemaEstudio.objects.filter(curso=curso, estado='aprobado')
        serializador = SerializadorTemaEstudio(temas, many=True)
        return Response(serializador.data)
