from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante, EsDocente
from apps.analitica.models import Resultado
from apps.analitica.serializers import SerializadorResultado
from apps.examenes.models import Curso


@extend_schema(
    tags=['Analítica'],
    summary='Mis resultados',
    description='Retorna todos los resultados del estudiante autenticado en todos sus exámenes, incluyendo nota, puntaje y respuestas por pregunta.',
    responses={
        200: SerializadorResultado(many=True),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
    },
)
class VistaMisResultados(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        resultados = Resultado.objects.filter(estudiante=request.user)
        serializador = SerializadorResultado(resultados, many=True)
        return Response(serializador.data)


@extend_schema(
    tags=['Analítica'],
    summary='Resultados de un curso',
    description='Retorna todos los resultados de todos los estudiantes en todos los exámenes del curso. Solo el docente dueño del curso puede acceder.',
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: SerializadorResultado(many=True),
        403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaResultadosCurso(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        resultados = Resultado.objects.filter(examen__curso=curso)
        serializador = SerializadorResultado(resultados, many=True)
        return Response(serializador.data)
