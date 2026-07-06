from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.analitica.models import Resultado
from apps.analitica.serializers import SerializadorResultado
from apps.examenes.models import Examen, Inscripcion


@extend_schema(
    tags=['Analítica'],
    summary='Mis resultados en un examen',
    description=(
        'Retorna todos los intentos del estudiante en un examen específico, '
        'con el puntaje y nota de cada intento y el promedio general. '
        'El estudiante debe estar inscrito en el curso del examen.'
    ),
    parameters=[
        OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del examen'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaMisResultadosExamen',
            fields={
                'examen_id': drf_serializers.IntegerField(),
                'examen_titulo': drf_serializers.CharField(),
                'total_intentos': drf_serializers.IntegerField(),
                'puntaje_promedio': drf_serializers.FloatField(),
                'nota_promedio': drf_serializers.FloatField(),
                'resultados': SerializadorResultado(many=True),
            },
        ),
        403: OpenApiResponse(description='No estás inscrito en el curso de este examen'),
        404: OpenApiResponse(description='Examen no encontrado o sin resultados'),
    },
)
class VistaMisResultadosExamen(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, examen_id):
        try:
            examen = Examen.objects.select_related('curso').get(id=examen_id)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=examen.curso).exists():
            return Response(
                {'detalle': 'No estás inscrito en el curso de este examen.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        resultados = Resultado.objects.filter(
            estudiante=request.user, examen=examen
        ).prefetch_related('respuestas')

        if not resultados.exists():
            return Response(
                {'detalle': 'Aún no has presentado este examen.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        puntaje_promedio = round(sum(r.puntaje for r in resultados) / resultados.count(), 2)
        nota_promedio = round(sum(r.nota for r in resultados) / resultados.count(), 2)

        return Response({
            'examen_id': examen.id,
            'examen_titulo': examen.titulo,
            'total_intentos': resultados.count(),
            'puntaje_promedio': puntaje_promedio,
            'nota_promedio': nota_promedio,
            'resultados': SerializadorResultado(resultados, many=True).data,
        })
