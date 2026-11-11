"""
Vista de análisis de acciones con IA sobre la analítica de un curso (HU-24).

Expone `POST /api/saber-pro/docente/cursos/<curso_id>/analitica/acciones/` con
los mismos filtros de la consulta de analítica (`?simulacro_id=`, `?periodo=`,
`?competencia_id=`, `?afirmacion_id=`, `?parte=` y `?area_id=`): la IA recibe
los indicadores agregados del curso con esos filtros y devuelve un resumen del
grupo y acciones recomendadas para el docente.

- Solo el docente propietario del curso puede generarlo.
- No se envían datos personales a la IA: el servicio compacta el payload a
  agregados y desgloses antes de invocar al modelo.
- Si el curso no tiene intentos elegibles con los filtros aplicados se
  responde 400 (no hay nada que analizar); si la IA no produce una respuesta
  válida tras sus reintentos, 502 sin efectos secundarios.
"""

from django.utils import timezone
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_analitica_saber_pro import (
    SerializadorAnalisisAcciones,
)
from apps.saber_pro.services.agente_analitica import generar_analisis_acciones_curso
from apps.saber_pro.services.analitica import (
    AfirmacionNoEncontradaError,
    CompetenciaNoEncontradaError,
    ParteNoCorrespondeError,
    construir_analitica_curso,
)
from apps.saber_pro.services.comparaciones import (
    AreaNoCorrespondeError,
    CursoNoEncontradoError,
    SimulacroNoEncontradoError,
)
from apps.saber_pro.views.parametros_analitica import (
    parametros_analitica_curso,
)
from core.permissions.permisos_rol import EsDocente


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Generar con IA el análisis de acciones de un curso Saber Pro',
    description=(
        'Analiza con IA la analítica del curso con los filtros aplicados y '
        'devuelve un resumen del grupo y una lista de acciones recomendadas '
        '(título, descripción y prioridad) para reforzar los criterios más '
        'débiles. La IA solo recibe datos agregados, nunca resultados '
        'individuales. Solo el docente propietario del curso puede generarlo.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por un simulacro del curso'),
        OpenApiParameter('periodo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Periodo académico AAAA-1 o AAAA-2'),
        OpenApiParameter('competencia_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por competencia'),
        OpenApiParameter('afirmacion_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por afirmación'),
        OpenApiParameter('parte', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por parte de Inglés (1 a 7)'),
        OpenApiParameter('area_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Valida el área del curso'),
    ],
    responses={
        200: SerializadorAnalisisAcciones,
        400: OpenApiResponse(description='Parámetro, área, criterio inválido o sin intentos elegibles'),
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        502: OpenApiResponse(description='La IA no produjo un análisis válido'),
    },
)
class VistaAnalisisAccionesSaberPro(APIView):
    permission_classes = [EsDocente]

    def post(self, request, curso_id):
        try:
            payload = construir_analitica_curso(
                request.user,
                curso_id,
                **parametros_analitica_curso(request),
            )
        except ValueError as error:
            return Response({'detalle': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except (
            AreaNoCorrespondeError,
            CompetenciaNoEncontradaError,
            AfirmacionNoEncontradaError,
            ParteNoCorrespondeError,
        ) as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_400_BAD_REQUEST)
        except (CursoNoEncontradoError, SimulacroNoEncontradoError) as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_404_NOT_FOUND)

        if payload['resumen']['total_intentos'] == 0:
            return Response(
                {
                    'detalle': (
                        'El curso no tiene intentos calificados con los filtros '
                        'aplicados: no hay datos para analizar.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analisis = generar_analisis_acciones_curso(payload)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=status.HTTP_502_BAD_GATEWAY)

        respuesta = {
            'curso': payload['curso'],
            'filtro': payload['filtro'],
            'generado_en': timezone.now(),
            'resumen': analisis['resumen'],
            'acciones': analisis['acciones'],
        }
        return Response(SerializadorAnalisisAcciones(respuesta).data)
