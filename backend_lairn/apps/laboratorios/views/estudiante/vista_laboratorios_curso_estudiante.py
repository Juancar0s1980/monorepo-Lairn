"""
Vista de listado de laboratorios de un curso, para el rol Estudiante.

Expone `/mis-cursos/<curso_id>/laboratorios/`. Requiere una inscripción
activa del estudiante en el curso, igual que `VistaExamenesCurso`.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Inscripcion
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.serializers import SerializadorLaboratorio


@extend_schema(
    tags=['Laboratorios'],
    summary='Laboratorios de un curso (estudiante)',
    description='Retorna los laboratorios disponibles en un curso. El estudiante debe estar inscrito.',
    responses={
        200: SerializadorLaboratorio(many=True),
        403: OpenApiResponse(description='No estás inscrito en este curso o no eres estudiante'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaLaboratoriosCursoEstudiante(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        laboratorios = Laboratorio.objects.filter(curso=curso)
        serializador = SerializadorLaboratorio(laboratorios, many=True)
        return Response(serializador.data)
