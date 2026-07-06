"""
Vista de listado de reportes, para el rol Administrador.

Expone el endpoint `/reportes/` (GET) con todos los reportes del sistema,
enriquecidos con el nombre de quien reportó y del curso/examen reportado.
Admite el filtro opcional `?estado=` para separar los pendientes de revisión
de los ya resueltos o descartados.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsAdministrador
from apps.moderacion.models.reporte import Reporte
from apps.moderacion.serializers.serializador_reporte_admin import SerializadorReporteAdmin


@extend_schema(
    tags=['Moderación'],
    summary='Listar reportes',
    description='Retorna todos los reportes de cursos y exámenes. Solo accesible para el Administrador.',
    parameters=[
        OpenApiParameter('estado', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Filtra por estado: pendiente, resuelto, descartado'),
    ],
    responses={
        200: SerializadorReporteAdmin(many=True),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaListaReportes(APIView):
    permission_classes = [EsAdministrador]

    # Lista todos los reportes, opcionalmente filtrados por estado.
    def get(self, request):
        reportes = Reporte.objects.select_related(
            'reportado_por', 'curso', 'examen'
        ).order_by('-creado_en')

        estado = request.query_params.get('estado')
        if estado:
            reportes = reportes.filter(estado=estado)

        serializador = SerializadorReporteAdmin(reportes, many=True)
        return Response(serializador.data)
