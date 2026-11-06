"""
Vista para responder el bloque actual de una presentación Saber Pro (HU-21.2).

Expone `POST /api/saber-pro/estudiante/presentaciones/<presentacion_id>/responder/`.
Solo acepta el bloque pendiente: no se puede retroceder ni responder dos veces
el mismo bloque. Al responder el último bloque, el intento se finaliza con
motivo `completada` y se devuelve el resultado.

Si el tiempo ya venció, la respuesta no se registra y se devuelve el resultado
con motivo `tiempo_agotado` (HU-21.4).
"""

from django.db import transaction
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.serializers import (
    SerializadorEstadoPresentacion,
    SerializadorResponderPresentacion,
)
from apps.saber_pro.services.presentaciones import (
    RespuestaInvalidaError,
    finalizar_si_vencida,
    pregunta_actual,
    registrar_respuesta,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Responder el bloque actual',
    description=(
        'Registra la respuesta del bloque actual y devuelve el siguiente bloque o el '
        'resultado final (HU-21.2). No permite retroceder ni reescribir respuestas. '
        'El cuerpo cambia según el subtipo de pregunta: opcion, relaciones, respuestas '
        'o texto.'
    ),
    parameters=[
        OpenApiParameter(
            'presentacion_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la presentación del estudiante autenticado.',
        ),
    ],
    request=SerializadorResponderPresentacion,
    responses={
        200: SerializadorEstadoPresentacion,
        400: OpenApiResponse(description='Respuesta inválida o presentación ya finalizada'),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Presentación no encontrada'),
    },
)
class VistaResponderPresentacionSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, presentacion_id):
        serializador = SerializadorResponderPresentacion(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = dict(serializador.validated_data)
        pregunta_id = datos.pop('pregunta_id', None)

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
            if presentacion.esta_en_progreso():
                try:
                    registrar_respuesta(presentacion, datos, pregunta_id)
                except RespuestaInvalidaError as error:
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
