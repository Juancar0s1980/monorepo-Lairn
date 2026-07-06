"""
Vista de actualización de estado de un reporte, para el rol Administrador.

Expone el endpoint `/reportes/<reporte_id>/` (PATCH) que permite marcar un
reporte como `resuelto` o `descartado` (o revertirlo a `pendiente`). Registra
`resuelto_en` automáticamente al salir del estado `pendiente`, y lo limpia si
el administrador lo revierte, para que el timestamp siempre refleje el
momento de la última decisión.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import serializers as drf_serializers
from core.permissions.permisos_rol import EsAdministrador
from apps.moderacion.models.reporte import Reporte, ESTADO_CHOICES
from apps.moderacion.serializers.serializador_reporte_admin import SerializadorReporteAdmin

ESTADOS_VALIDOS = {clave for clave, _ in ESTADO_CHOICES}


@extend_schema(
    tags=['Moderación'],
    summary='Actualizar estado de un reporte',
    description='Marca un reporte como resuelto, descartado o lo revierte a pendiente.',
    request=inline_serializer(name='ActualizarEstadoReporte', fields={'estado': drf_serializers.CharField()}),
    parameters=[
        OpenApiParameter('reporte_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del reporte'),
    ],
    responses={
        200: SerializadorReporteAdmin,
        400: OpenApiResponse(description='Estado inválido'),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
        404: OpenApiResponse(description='Reporte no encontrado'),
    },
)
class VistaDetalleReporte(APIView):
    permission_classes = [EsAdministrador]

    # Actualiza el estado de un reporte y registra el momento de la decisión.
    def patch(self, request, reporte_id):
        try:
            reporte = Reporte.objects.get(id=reporte_id)
        except Reporte.DoesNotExist:
            return Response({'detalle': 'Reporte no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        estado = request.data.get('estado')
        if estado not in ESTADOS_VALIDOS:
            return Response(
                {'detalle': f'Estado inválido. Debe ser uno de: {", ".join(ESTADOS_VALIDOS)}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reporte.estado = estado
        reporte.resuelto_en = timezone.now() if estado != 'pendiente' else None
        reporte.save()

        serializador = SerializadorReporteAdmin(reporte)
        return Response(serializador.data)
