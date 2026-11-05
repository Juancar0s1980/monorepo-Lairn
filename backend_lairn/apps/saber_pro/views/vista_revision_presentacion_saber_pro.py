"""
Revisión y calificación docente de consignas abiertas Saber Pro (HU-24).

`GET` devuelve las respuestas escritas del intento y su calificación actual.
`POST` registra UNA calificación 0.0-5.0 y UNA retroalimentación para el intento
completo y recalcula su puntaje. Cada intento se califica por separado. Solo el
docente propietario del curso puede operar sobre sus simulacros.
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.serializers.serializador_revision_saber_pro import (
    SerializadorDetalleRevision,
    SerializadorRevisionPresentacion,
)
from apps.saber_pro.services.presentaciones import (
    RevisionInvalidaError,
    registrar_revision,
)
from core.permissions.permisos_rol import EsDocente


def _obtener_presentacion(request, curso_id, simulacro_id, presentacion_id):
    return (
        PresentacionSimulacro.objects.filter(
            id=presentacion_id,
            simulacro_id=simulacro_id,
            simulacro__curso_id=curso_id,
            simulacro__curso__docente=request.user,
            estado='finalizada',
        )
        .select_related('simulacro', 'estudiante', 'revisada_por')
        .prefetch_related('preguntas')
        .first()
    )


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Consultar y calificar un intento con consignas abiertas',
    description=(
        'GET retorna las respuestas escritas del intento finalizado. POST '
        'registra una calificación 0.0-5.0 y una retroalimentación para el '
        'intento completo, y recalcula su puntaje.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH),
        OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH),
        OpenApiParameter('presentacion_id', OpenApiTypes.INT, OpenApiParameter.PATH),
    ],
    request=SerializadorRevisionPresentacion,
    responses={
        200: SerializadorDetalleRevision,
        400: OpenApiResponse(description='Calificación inválida o intento sin consignas'),
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Intento finalizado no encontrado'),
    },
)
class VistaRevisionPresentacionSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id, simulacro_id, presentacion_id):
        presentacion = _obtener_presentacion(request, curso_id, simulacro_id, presentacion_id)
        if presentacion is None:
            return Response(
                {'detalle': 'Intento finalizado no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SerializadorDetalleRevision(presentacion).data)

    def post(self, request, curso_id, simulacro_id, presentacion_id):
        presentacion = _obtener_presentacion(request, curso_id, simulacro_id, presentacion_id)
        if presentacion is None:
            return Response(
                {'detalle': 'Intento finalizado no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        entrada = SerializadorRevisionPresentacion(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            registrar_revision(
                presentacion,
                entrada.validated_data['calificacion'],
                entrada.validated_data.get('retroalimentacion', ''),
                request.user,
            )
        except RevisionInvalidaError as error:
            return Response(
                {'detalle': error.mensaje},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentacion = _obtener_presentacion(request, curso_id, simulacro_id, presentacion_id)
        return Response(SerializadorDetalleRevision(presentacion).data)