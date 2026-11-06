"""
Vista para finalizar manualmente una presentación Saber Pro (HU-21.3).

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/finalizar/`
sin cuerpo. Es idempotente: si la presentación ya terminó, retorna su resultado.

Si el tiempo ya venció, el motivo queda en `tiempo_agotado`; en caso contrario,
la finalización anticipada queda en `manual`. El frontend también llama a este
endpoint cuando el contador llega a cero (HU-21.4).
"""

from django.db import transaction
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.serializers import SerializadorEstadoPresentacion
from apps.saber_pro.services.presentaciones import (
    MOTIVO_MANUAL,
    finalizar_presentacion,
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Finalizar una presentación',
    description=(
        'Finaliza el intento del estudiante y calcula el puntaje sobre los ítems '
        'evaluables (HU-21.3). Si ya venció, el motivo es `tiempo_agotado`; si el '
        'estudiante decide terminar antes, `manual`. Es idempotente.'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentación del estudiante autenticado.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorEstadoPresentacion,
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentación no encontrada'),
    },
)
class VistaFinalizarPresentacionSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, presentacion_id):
        with transaction.atomic():
            presentacion = (
                PresentacionSimulacro.objects.select_for_update()
                .filter(id=presentacion_id, estudiante=request.user)
                .select_related('simulacro__curso__area')
                .first()
            )
            if presentacion is None:
                return Response(
                    {'detalle': 'Presentación no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not finalizar_si_vencida(presentacion) and presentacion.esta_en_progreso():
                finalizar_presentacion(presentacion, MOTIVO_MANUAL)

        presentacion = (
            PresentacionSimulacro.objects.select_related('simulacro__curso__area')
            .prefetch_related('preguntas')
            .get(pk=presentacion.pk)
        )
        return Response(
            SerializadorEstadoPresentacion(
                presentacion,
                context={'pregunta': pregunta_actual(presentacion)},
            ).data
        )
