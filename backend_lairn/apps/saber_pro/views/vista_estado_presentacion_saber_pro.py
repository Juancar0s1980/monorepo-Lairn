"""
Vista de estado de una presentación Saber Pro (HU-21.3).

Expone `GET /api/saber-pro/estudiante/presentaciones/<presentacion_id>/`.
Devuelve el bloque actual y el tiempo restante, o el resultado final si el
intento ya terminó. Al consultar una presentación vencida se finaliza de forma
perezosa por tiempo agotado.
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
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Consultar estado de una presentación',
    description=(
        'Retorna el avance, el cronómetro y el bloque actual de la presentación del '
        'estudiante. Si el tiempo venció, finaliza el intento y retorna el resultado '
        '(HU-21.3/HU-21.4).'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentación del estudiante autenticado.',
        ),
    ],
    responses={
        200: SerializadorEstadoPresentacion,
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentación no encontrada'),
    },
)
class VistaEstadoPresentacionSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, presentacion_id):
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
            finalizar_si_vencida(presentacion)

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
