"""
Vista del catálogo de criterios de un área Saber Pro, para el rol Docente (HU-20.1).

Expone `GET /docente/areas/<area_id>/criterios/`: devuelve la estructura de
evaluación del área y los criterios que el docente puede seleccionar al
generar contenido con IA:

- Áreas estructuradas: competencias con sus afirmaciones y evidencias.
- Inglés: las 7 partes con su peso y cantidad de opciones.
- Comunicación Escrita: sin criterios (se genera una consigna).

El frontend construye con esta respuesta el formulario de generación, de modo
que la forma del área vive en un solo lugar (`services/catalogo_saber_pro.py`)
y no se duplica en el cliente.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.serializers import SerializadorCriteriosArea
from apps.saber_pro.services.catalogo_saber_pro import (
    ESTRUCTURA_COMPETENCIAS,
    ESTRUCTURA_PARTES,
    criterios_area,
    obtener_estructura_area,
    partes_ingles,
)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Criterios de evaluación de un área',
    description=(
        'Devuelve la estructura de evaluación del área y los criterios que el docente '
        'selecciona al generar contenido: competencias/afirmaciones/evidencias en áreas '
        'estructuradas, las 7 partes en Inglés, o ningún criterio en Comunicación Escrita.'
    ),
    responses={
        200: SerializadorCriteriosArea,
        404: OpenApiResponse(description='Área no encontrada'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
    },
)
class VistaCriteriosAreaSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, area_id):
        try:
            area = AreaSaberPro.objects.get(id=area_id)
        except AreaSaberPro.DoesNotExist:
            return Response({'detalle': 'Área Saber Pro no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        estructura = obtener_estructura_area(area)
        datos = {
            'area': area,
            'tipo_estructura': estructura,
            'competencias': criterios_area(area) if estructura == ESTRUCTURA_COMPETENCIAS else [],
            'partes': partes_ingles() if estructura == ESTRUCTURA_PARTES else [],
        }
        return Response(SerializadorCriteriosArea(datos).data)