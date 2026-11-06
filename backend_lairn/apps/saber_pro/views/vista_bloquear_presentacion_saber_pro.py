"""
Vista para bloquear una presentacion Saber Pro por una salida detectada (HU-22).

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/bloquear/`.
El frontend la llama cuando el estudiante abandona la pantalla completa, cambia
de pestana o minimiza la ventana. El backend solo marca el intento como
bloqueado si el simulacro tiene un codigo de desbloqueo configurado; de lo
contrario la advertencia sigue siendo visual y el estudiante no queda atrapado.
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
    bloquear_presentacion,
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Bloquear una presentacion por salida detectada',
    description=(
        'Marca el intento como bloqueado cuando el estudiante sale de la pantalla '
        'completa o cambia de pestana. Solo aplica si el docente configuro un codigo '
        'de desbloqueo. La operacion es idempotente (HU-22).'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentacion del estudiante autenticado.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorEstadoPresentacion,
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentacion no encontrada'),
    },
)
class VistaBloquearPresentacionSaberPro(APIView):
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
                    {'detalle': 'Presentacion no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            finalizar_si_vencida(presentacion)
            if presentacion.esta_en_progreso():
                bloquear_presentacion(presentacion)

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
