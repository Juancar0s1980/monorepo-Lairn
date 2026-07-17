"""
Vista de evolución de la nota del curso en el tiempo, para el rol Docente.

Expone `GET /analitica/curso/<curso_id>/evolucion/`: agrupa los `Resultado`
del curso por semana de `completado_en` y reporta la nota promedio de cada
semana, para poder graficar una tendencia en vez de solo la foto fija que ya
muestran `resumen` y `patrones`.
"""

from django.db.models import Count, Avg
from django.db.models.functions import TruncWeek
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.analitica.models import Resultado
from apps.examenes.models import Curso

UMBRAL_TENDENCIA = 0.2


@extend_schema(
    tags=['Analítica'],
    summary='Evolución de la nota del curso en el tiempo',
    description=(
        'Agrupa los resultados del curso por semana y reporta la nota promedio de cada '
        'semana, para visualizar si el grupo mejora, empeora o se mantiene estable.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: OpenApiResponse(description='Serie temporal de nota promedio por semana'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaEvolucionCurso(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        resultados_qs = Resultado.objects.filter(examen__curso=curso)

        if not resultados_qs.exists():
            return Response({
                'curso': curso.nombre,
                'puntos': [],
                'tendencia': None,
                'mensaje': 'Aún no hay exámenes presentados en este curso.',
            })

        puntos_raw = resultados_qs.annotate(
            semana=TruncWeek('completado_en')
        ).values('semana').annotate(
            total=Count('id'),
            nota_promedio=Avg('nota'),
        ).order_by('semana')

        puntos = [
            {
                'periodo': p['semana'].date().isoformat(),
                'nota_promedio': round(p['nota_promedio'], 2),
                'total_resultados': p['total'],
            }
            for p in puntos_raw
        ]

        tendencia = None
        if len(puntos) >= 2:
            diferencia = puntos[-1]['nota_promedio'] - puntos[0]['nota_promedio']
            if diferencia >= UMBRAL_TENDENCIA:
                tendencia = 'mejorando'
            elif diferencia <= -UMBRAL_TENDENCIA:
                tendencia = 'empeorando'
            else:
                tendencia = 'estable'

        return Response({
            'curso': curso.nombre,
            'puntos': puntos,
            'tendencia': tendencia,
        })
