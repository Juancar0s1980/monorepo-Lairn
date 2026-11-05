"""
Vista de disponibilidad de contenido aprobado para un simulacro (HU-19.2).

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/simulacros/disponibilidad/`.
Devuelve cuántas preguntas aprobadas hay por competencia, afirmación o parte de
Inglés según la estructura del área del curso. El formulario del docente la usa
para no configurar una distribución que el banco no puede cubrir.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorDisponibilidadSimulacro
from apps.saber_pro.services.simulacros import disponibilidad_area
from core.permissions.permisos_rol import EsDocente


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Disponibilidad de contenido para un simulacro',
    description=(
        'Retorna el total de preguntas aprobadas y su desglose por competencia, '
        'afirmación o parte de Inglés para el área del curso. En Inglés incluye las '
        '7 partes obligatorias con su cantidad fija de preguntas. Permite validar la '
        'distribución antes de crear el simulacro (HU-19.2/19.3).'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
    ],
    responses={
        200: SerializadorDisponibilidadSimulacro,
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaDisponibilidadSimulacroSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.select_related('area').get(
                id=curso_id,
                docente=request.user,
            )
        except CursoSaberPro.DoesNotExist:
            return Response(
                {'detalle': 'Curso no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        datos = disponibilidad_area(curso)
        datos['area'] = curso.area
        return Response(SerializadorDisponibilidadSimulacro(datos).data)
