"""
Vista para desbloquear una presentacion Saber Pro con el codigo docente (HU-22).

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/desbloquear/`
con `{ "codigo": "..." }`. Valida el codigo contra el hash configurado en el
simulacro y reanuda el intento sin alterar sus respuestas ni su cronometro.
"""

from django.db import transaction
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.serializers import (
    SerializadorDesbloqueoPresentacion,
    SerializadorEstadoPresentacion,
)
from apps.saber_pro.services.presentaciones import (
    CodigoDesbloqueoInvalidoError,
    desbloquear_presentacion,
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Desbloquear una presentacion con el codigo docente',
    description=(
        'Valida el codigo definido por el docente y reanuda el intento bloqueado. '
        'El cronometro sigue corriendo; el desbloqueo no otorga tiempo adicional '
        '(HU-22).'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentacion del estudiante autenticado.',
        ),
    ],
    request=SerializadorDesbloqueoPresentacion,
    responses={
        200: SerializadorEstadoPresentacion,
        400: OpenApiResponse(description='Codigo invalido o presentacion finalizada'),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentacion no encontrada'),
    },
)
class VistaDesbloquearPresentacionSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, presentacion_id):
        serializador = SerializadorDesbloqueoPresentacion(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        codigo = serializador.validated_data['codigo']

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
                try:
                    desbloquear_presentacion(presentacion, codigo)
                except CodigoDesbloqueoInvalidoError as error:
                    return Response(
                        {'detalle': error.mensaje},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
