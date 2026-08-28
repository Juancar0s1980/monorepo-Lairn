"""
Vista de progreso del laboratorio, para el rol Estudiante.

Expone `GET /laboratorios/laboratorios/<laboratorio_id>/mi-progreso/`: por
cada pregunta del laboratorio, si el estudiante autenticado ya la intentó y
cuál fue su MEJOR puntaje (mismo criterio "mejor entrega" que
`vista_analitica_laboratorio.py` usa para el docente — un reintento que
mejora no debe hacer ver la pregunta como "peor" de lo que realmente le fue
al estudiante).

Pensado para pintar el selector de preguntas del laboratorio de un vistazo
(gris = no intentada, ámbar = intentada pero no perfecta, verde = 100%) sin
tener que pedir `/mis-entregas/` pregunta por pregunta — una sola consulta a
`Entrega`, agregada en Python.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import Laboratorio, Entrega


@extend_schema(
    tags=['Laboratorios'],
    summary='Mi progreso en el laboratorio (mejor puntaje por pregunta)',
    parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: OpenApiResponse(description='Mejor puntaje del estudiante autenticado por pregunta'),
        403: OpenApiResponse(description='No estás inscrito en este curso'),
        404: OpenApiResponse(description='Laboratorio no encontrado'),
    },
)
class VistaMiProgresoLaboratorio(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.select_related('curso').get(id=laboratorio_id)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=laboratorio.curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        mejor_por_pregunta = {}
        entregas = Entrega.objects.filter(
            pregunta__laboratorio=laboratorio, estudiante=request.user
        ).only('pregunta_id', 'puntaje')
        for entrega in entregas:
            actual = mejor_por_pregunta.get(entrega.pregunta_id)
            if actual is None or entrega.puntaje > actual:
                mejor_por_pregunta[entrega.pregunta_id] = entrega.puntaje

        progreso = [
            {
                'pregunta_id': pregunta_id,
                'intentado': pregunta_id in mejor_por_pregunta,
                'mejor_puntaje': mejor_por_pregunta.get(pregunta_id),
            }
            for pregunta_id in laboratorio.preguntas.values_list('id', flat=True)
        ]

        return Response({'progreso': progreso})
