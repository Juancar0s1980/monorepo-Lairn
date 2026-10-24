"""
Vista de listado de laboratorios de un curso, para el rol Estudiante.

Expone `/mis-cursos/<curso_id>/laboratorios/`. Requiere una inscripción
activa del estudiante en el curso, igual que `VistaExamenesCurso`.

Además del conteo de preguntas, agrega cuántas de esas preguntas ya
respondió el estudiante autenticado (`preguntas_respondidas`) — así la
tarjeta de la lista puede mostrar progreso sin que el estudiante tenga que
entrar a cada laboratorio para saber si ya lo hizo. Se resuelve con UNA sola
consulta agregada para todos los laboratorios del curso (no una por
laboratorio), ver `SerializadorLaboratorioListaEstudiante`.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Inscripcion
from apps.laboratorios.models import Laboratorio, Entrega
from apps.laboratorios.serializers import SerializadorLaboratorioListaEstudiante


@extend_schema(
    tags=['Laboratorios'],
    summary='Laboratorios de un curso (estudiante)',
    description='Retorna los laboratorios disponibles en un curso, con el progreso del estudiante en cada uno. El estudiante debe estar inscrito.',
    responses={
        200: SerializadorLaboratorioListaEstudiante(many=True),
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

        # Preguntas distintas que el estudiante ya respondió, por laboratorio
        # (una entrega o más en una pregunta cuenta 1 vez) — una sola consulta.
        respondidas_por_lab: dict[int, int] = {}
        preguntas_respondidas = (
            Entrega.objects
            .filter(pregunta__laboratorio__in=laboratorios, estudiante=request.user)
            .values('pregunta__laboratorio_id', 'pregunta_id')
            .distinct()
        )
        for fila in preguntas_respondidas:
            lab_id = fila['pregunta__laboratorio_id']
            respondidas_por_lab[lab_id] = respondidas_por_lab.get(lab_id, 0) + 1

        serializador = SerializadorLaboratorioListaEstudiante(
            laboratorios, many=True, context={'respondidas_por_lab': respondidas_por_lab}
        )
        return Response(serializador.data)
