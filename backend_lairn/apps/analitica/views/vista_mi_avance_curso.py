from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.analitica.models import Resultado
from apps.analitica.serializers import SerializadorResultado
from apps.examenes.models import Curso, Inscripcion


@extend_schema(
    tags=['Analítica'],
    summary='Mi avance en un curso',
    description=(
        'Retorna todos los resultados del estudiante en los exámenes de un curso específico, '
        'junto con el puntaje promedio y el total de exámenes presentados. '
        'El estudiante debe estar inscrito en el curso.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaMiAvanceCurso',
            fields={
                'curso_id': drf_serializers.IntegerField(),
                'curso_nombre': drf_serializers.CharField(),
                'total_examenes_presentados': drf_serializers.IntegerField(),
                'puntaje_promedio': drf_serializers.FloatField(),
                'nota_promedio': drf_serializers.FloatField(),
                'resultados': SerializadorResultado(many=True),
            },
        ),
        403: OpenApiResponse(description='No estás inscrito en este curso'),
        404: OpenApiResponse(description='Curso no encontrado o sin resultados'),
    },
)
class VistaMiAvanceCurso(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response(
                {'detalle': 'No estás inscrito en este curso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        resultados = Resultado.objects.filter(
            estudiante=request.user, examen__curso=curso
        ).select_related('examen').prefetch_related('respuestas')

        if not resultados.exists():
            return Response(
                {'detalle': 'Aún no has presentado ningún examen en este curso.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        puntaje_promedio = round(sum(r.puntaje for r in resultados) / resultados.count(), 2)
        nota_promedio = round(sum(r.nota for r in resultados) / resultados.count(), 2)

        return Response({
            'curso_id': curso.id,
            'curso_nombre': curso.nombre,
            'total_examenes_presentados': resultados.count(),
            'puntaje_promedio': puntaje_promedio,
            'nota_promedio': nota_promedio,
            'resultados': SerializadorResultado(resultados, many=True).data,
        })
