"""
Vista de simulacros disponibles para el estudiante (HU-19.5).

Expone `GET /api/saber-pro/estudiante/simulacros/` con filtro opcional
`?curso_id=`. Solo devuelve simulacros activos de cursos activos a los que el
estudiante está inscrito; un estudiante ajeno al curso nunca los visualiza.

Antes de responder, cierra por salida cualquier intento que haya quedado activo.
Así el listado nunca ofrece reanudar un examen abandonado: el intento se envía y
solo se cierra ese intento; si quedan intentos disponibles, el estudiante puede
iniciar el siguiente.

La respuesta no incluye preguntas, opciones, respuestas correctas ni la
distribución: la presentación y el detalle llegan en la HU-21.
"""

from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers import SerializadorSimulacroEstudiante
from apps.saber_pro.services.presentaciones import finalizar_por_salida
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Simulacros disponibles para el estudiante',
    description=(
        'Lista los simulacros activos de los cursos Saber Pro activos a los que el '
        'estudiante autenticado está inscrito (HU-19.5). Se puede filtrar por curso '
        'con `curso_id`. No expone preguntas ni respuestas correctas.'
    ),
    parameters=[
        OpenApiParameter(
            'curso_id',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra los simulacros de un curso específico.',
        ),
    ],
    responses={
        200: SerializadorSimulacroEstudiante(many=True),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
    },
)
class VistaSimulacrosEstudianteSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        simulacros = (
            Simulacro.objects.filter(
                curso__inscripciones__estudiante=request.user,
                curso__activo=True,
                activo=True,
            )
            .select_related('curso__area')
            .prefetch_related(
                'preguntas_asignadas__contenido',
                Prefetch(
                    'presentaciones',
                    queryset=PresentacionSimulacro.objects.filter(
                        estudiante=request.user,
                    ).order_by('intento'),
                    to_attr='presentaciones_estudiante',
                ),
            )
            .distinct()
        )

        curso_id = request.query_params.get('curso_id')
        if curso_id:
            try:
                simulacros = simulacros.filter(curso_id=int(curso_id))
            except (TypeError, ValueError):
                return Response(
                    {'detalle': 'El parámetro curso_id debe ser un número entero.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ids_simulacros = list(simulacros.values_list('id', flat=True))
        if ids_simulacros:
            with transaction.atomic():
                activas = (
                    PresentacionSimulacro.objects.select_for_update()
                    .filter(
                        estudiante=request.user,
                        estado='en_progreso',
                        simulacro_id__in=ids_simulacros,
                    )
                    .select_related('simulacro')
                )
                for presentacion in activas:
                    finalizar_por_salida(presentacion)

        return Response(SerializadorSimulacroEstudiante(simulacros, many=True).data)
