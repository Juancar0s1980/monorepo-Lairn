from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.analitica.models import Resultado
from apps.analitica.serializers import SerializadorResultado
from apps.examenes.models import Curso


@extend_schema(
    tags=['Analítica'],
    summary='Avance de un estudiante en el curso',
    description='Retorna todos los resultados de un estudiante específico en el curso, junto con su puntaje promedio y total de exámenes presentados.',
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        OpenApiParameter('estudiante_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del estudiante'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaAvanceEstudiante',
            fields={
                'estudiante_id': drf_serializers.IntegerField(),
                'curso_id': drf_serializers.IntegerField(),
                'total_examenes_presentados': drf_serializers.IntegerField(),
                'puntaje_promedio': drf_serializers.FloatField(),
                'resultados': SerializadorResultado(many=True),
            },
        ),
        403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado o sin resultados para este estudiante'),
    },
)
class VistaAvanceEstudiante(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id, estudiante_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        resultados = Resultado.objects.filter(
            examen__curso=curso,
            estudiante_id=estudiante_id
        ).select_related('examen').prefetch_related('respuestas')

        if not resultados.exists():
            return Response({'detalle': 'Sin resultados para este estudiante en el curso.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorResultado(resultados, many=True)

        puntaje_promedio = sum(r.puntaje for r in resultados) / resultados.count()

        return Response({
            'estudiante_id': estudiante_id,
            'curso_id': curso_id,
            'total_examenes_presentados': resultados.count(),
            'puntaje_promedio': round(puntaje_promedio, 2),
            'resultados': serializador.data,
        })
