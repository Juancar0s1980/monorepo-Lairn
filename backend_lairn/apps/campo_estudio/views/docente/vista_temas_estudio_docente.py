"""
Vista de la cola de temas de estudio de un curso, para el rol Docente.

Expone `GET /cursos/<curso_id>/campo-estudio/temas/`: lista TODOS los temas
(pendientes y aprobados), a diferencia de la vista del estudiante que solo
ve los aprobados. Es la cola de revisión que el docente puede retomar en
cualquier momento, no un modal efímero.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.campo_estudio.models import TemaEstudio
from apps.campo_estudio.serializers import SerializadorTemaEstudio


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Listar temas de estudio del curso (docente)',
    description='Retorna todos los temas del curso, pendientes y aprobados, para la cola de revisión del docente.',
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={200: SerializadorTemaEstudio(many=True), 404: OpenApiResponse(description='Curso no encontrado')},
)
class VistaTemasEstudioDocente(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        temas = TemaEstudio.objects.filter(curso=curso)
        serializador = SerializadorTemaEstudio(temas, many=True)
        return Response(serializador.data)
