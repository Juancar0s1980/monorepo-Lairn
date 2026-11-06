"""
Vista de solo lectura de las preguntas asignadas a un simulacro Saber Pro.

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/simulacros/<simulacro_id>/preguntas/`.

El docente autenticado consulta el cuestionario congelado del simulacro: cada
pregunta aprobada que quedó asignada, su orden de presentación y el contenido
completo, incluida la respuesta correcta. La selección se persiste al crear o
editar el simulacro, por lo que esta vista no vuelve a sortear contenido.

Solo el docente dueño del curso puede consultarlo (`curso__docente=request.user`);
un curso o simulacro ajeno responde 404.
"""

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers import SerializadorPreguntasSimulacro
from core.permissions.permisos_rol import EsDocente


class VistaPreguntasSimulacroSaberPro(APIView):
    permission_classes = [EsDocente]

    @extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Consultar preguntas asignadas a un simulacro',
        description=(
            'Retorna las preguntas aprobadas que quedaron asignadas al simulacro, '
            'en su orden de presentación y con su contenido completo (incluidas las '
            'respuestas correctas). Es una vista de solo lectura para el docente '
            'dueño del curso (HU-19.4).'
        ),
        parameters=[
            OpenApiParameter(
                'curso_id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                description='ID del curso Saber Pro',
            ),
            OpenApiParameter(
                'simulacro_id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                description='ID del simulacro',
            ),
        ],
        responses={
            200: SerializadorPreguntasSimulacro,
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        },
    )
    def get(self, request, curso_id, simulacro_id):
        try:
            simulacro = (
                Simulacro.objects.filter(
                    id=simulacro_id,
                    curso_id=curso_id,
                    curso__docente=request.user,
                )
                .select_related('curso__area')
                .prefetch_related(
                    'preguntas_asignadas__contenido__area',
                    'preguntas_asignadas__contenido__competencia',
                    'preguntas_asignadas__contenido__afirmacion',
                    'preguntas_asignadas__contenido__evidencia',
                )
                .get()
            )
        except Simulacro.DoesNotExist:
            return Response(
                {'detalle': 'Simulacro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        preguntas = list(simulacro.preguntas_asignadas.all())
        datos = {
            'simulacro_id': simulacro.id,
            'titulo': simulacro.titulo,
            'total_preguntas': simulacro.total_preguntas_asignadas(),
            'preguntas': preguntas,
        }
        return Response(SerializadorPreguntasSimulacro(datos).data)
