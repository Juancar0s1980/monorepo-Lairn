"""
Vista de detalle de un laboratorio, para el rol Estudiante.

Expone `/mis-cursos/<curso_id>/laboratorios/<laboratorio_id>/`. Usa
`SerializadorLaboratorioDetalleEstudiante`, que filtra los casos de test
ocultos de cada pregunta — el estudiante solo ve los marcados como ejemplo
público.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Inscripcion
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.serializers import SerializadorLaboratorioDetalleEstudiante


@extend_schema(
    tags=['Laboratorios'],
    summary='Detalle de laboratorio (estudiante)',
    description='Retorna el laboratorio con sus preguntas y solo los casos de test públicos.',
    responses={
        200: SerializadorLaboratorioDetalleEstudiante,
        403: OpenApiResponse(description='No estás inscrito en este curso o no eres estudiante'),
        404: OpenApiResponse(description='Curso o laboratorio no encontrado'),
    },
)
class VistaDetalleLaboratorioEstudiante(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, curso_id, laboratorio_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            laboratorio = Laboratorio.objects.get(id=laboratorio_id, curso=curso)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorLaboratorioDetalleEstudiante(laboratorio)
        return Response(serializador.data)
