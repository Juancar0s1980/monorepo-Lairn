"""
Vista para solicitar el desbloqueo de un simulacro Saber Pro.

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/solicitar-desbloqueo/`.
El frontend la llama cuando detecta cambio de pestaña, salida de pantalla
completa o pérdida de foco. El intento se bloquea sin finalizarse y se crea una
solicitud que el docente dueño del curso puede aprobar de forma remota.

Es idempotente mientras exista una solicitud pendiente: volver a salir no crea
solicitudes duplicadas ni altera el avance del intento.
"""

from django.db import transaction
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.serializers import (
    SerializadorEstadoPresentacion,
    SerializadorSolicitarDesbloqueo,
)
from apps.saber_pro.services.desbloqueos import (
    DesbloqueoInvalidoError,
    solicitar_desbloqueo,
)
from apps.saber_pro.services.presentaciones import (
    finalizar_si_vencida,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Solicitar desbloqueo de un simulacro bloqueado',
    description=(
        'Bloquea el intento cuando el estudiante cambia de pestaña, sale de pantalla '
        'completa o pierde el foco, y crea una solicitud para que el docente la apruebe. '
        'El intento conserva su avance y cronómetro; no se finaliza.'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentación del estudiante autenticado.',
        ),
    ],
    request=SerializadorSolicitarDesbloqueo,
    responses={
        200: SerializadorEstadoPresentacion,
        400: OpenApiResponse(description='La presentación ya finalizó'),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentación no encontrada'),
    },
)
class VistaSolicitarDesbloqueoSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, presentacion_id):
        serializador = SerializadorSolicitarDesbloqueo(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        motivo = serializador.validated_data['motivo']

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
                try:
                    solicitar_desbloqueo(presentacion, motivo)
                except DesbloqueoInvalidoError as error:
                    return Response(
                        {'detalle': error.mensaje},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        presentacion = (
            PresentacionSimulacro.objects.select_related('simulacro__curso__area')
            .prefetch_related('preguntas', 'solicitudes_desbloqueo')
            .get(pk=presentacion.pk)
        )
        return Response(
            SerializadorEstadoPresentacion(
                presentacion,
                context={'pregunta': pregunta_actual(presentacion)},
            ).data
        )
