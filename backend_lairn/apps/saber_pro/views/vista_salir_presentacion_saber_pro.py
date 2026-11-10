"""
Vista para cerrar una presentación Saber Pro cuando el estudiante sale (HU-22).

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/salir/`
sin cuerpo. El frontend la llama cuando el estudiante cambia de pestaña, sale de
la pantalla completa, intenta volver atrás o cierra la página. El intento se
finaliza con motivo `salida` y no puede reanudarse; si al estudiante le quedan
intentos disponibles, puede iniciar uno nuevo. Es idempotente: si ya terminó,
retorna su resultado.
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
    finalizar_por_salida,
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Cerrar una presentación por salida del estudiante',
    description=(
        'Finaliza el intento con motivo `salida` cuando el estudiante abandona la '
        'pantalla del simulacro (HU-22). El intento no se puede reanudar; si al '
        'estudiante le quedan intentos disponibles, puede iniciar el siguiente. Es '
        'idempotente.'
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
class VistaSalirPresentacionSaberPro(APIView):
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

            if not finalizar_si_vencida(presentacion):
                finalizar_por_salida(presentacion)

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
