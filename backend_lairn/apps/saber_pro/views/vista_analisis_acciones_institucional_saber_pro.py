"""
Vista de análisis de acciones con IA sobre la analítica institucional (HU-24.7).

Expone `POST /api/saber-pro/institucional/analitica/acciones/` con los mismos
filtros de la consulta institucional (`?curso_id=`, `?programa_id=`,
`?area_id=`, `?competencia_id=`, `?afirmacion_id=`, `?parte=` y `?periodo=`):
la IA recibe los indicadores agregados de la institución con esos filtros y
devuelve un resumen del conjunto y acciones recomendadas para coordinación y
vicerrectoría.

- Accesible para Coordinador y Vicerrector (y Administrador en lectura) con
  `EsLectorAnaliticaConIA`.
- No se envían datos personales a la IA: la analítica institucional solo tiene
  agregados y desgloses, nunca resultados individuales.
- Si no hay intentos elegibles con los filtros aplicados se responde 400 (no
  hay nada que analizar); si la IA no produce una respuesta válida tras sus
  reintentos, 502 sin efectos secundarios.
"""

from django.utils import timezone
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_analitica_saber_pro import (
    SerializadorAnalisisAccionesInstitucional,
)
from apps.saber_pro.services.agente_analitica import (
    generar_analisis_acciones_institucional,
)
from apps.saber_pro.services.analitica import (
    AfirmacionNoEncontradaError,
    CompetenciaNoEncontradaError,
    ParteNoCorrespondeError,
    ProgramaNoEncontradoError,
    construir_analitica_institucional,
)
from apps.saber_pro.services.comparaciones import (
    AreaNoCorrespondeError,
    CursoNoEncontradoError,
)
from apps.saber_pro.views.parametros_analitica import (
    parametros_analitica_institucional,
)
from core.permissions.permisos_rol import EsLectorAnaliticaConIA


@extend_schema(
    tags=['Saber Pro - Institucional'],
    summary='Generar con IA el análisis de acciones de la analítica institucional',
    description=(
        'Analiza con IA la analítica consolidada de la institución con los '
        'filtros aplicados y devuelve un resumen del desempeño y una lista de '
        'acciones recomendadas (título, descripción y prioridad) para '
        'coordinación y vicerrectoría. La IA solo recibe datos agregados, '
        'nunca resultados individuales.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por un curso Saber Pro'),
        OpenApiParameter('programa_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por carrera (programa académico)'),
        OpenApiParameter('area_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por área Saber Pro'),
        OpenApiParameter('competencia_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por competencia'),
        OpenApiParameter('afirmacion_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por afirmación'),
        OpenApiParameter('parte', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra el desglose por parte de Inglés (1 a 7)'),
        OpenApiParameter('periodo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Periodo académico AAAA-1 o AAAA-2'),
    ],
    responses={
        200: SerializadorAnalisisAccionesInstitucional,
        400: OpenApiResponse(description='Parámetro, área, criterio inválido o sin intentos elegibles'),
        404: OpenApiResponse(description='Curso o programa no encontrado'),
        502: OpenApiResponse(description='La IA no produjo un análisis válido'),
    },
)
class VistaAnalisisAccionesInstitucionalSaberPro(APIView):
    permission_classes = [EsLectorAnaliticaConIA]

    def post(self, request):
        try:
            payload = construir_analitica_institucional(
                **parametros_analitica_institucional(request),
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
        except (CursoNoEncontradoError, ProgramaNoEncontradoError) as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_404_NOT_FOUND)

        if payload['resumen']['total_intentos'] == 0:
            return Response(
                {
                    'detalle': (
                        'No hay intentos calificados con los filtros aplicados: '
                        'no hay datos para analizar.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analisis = generar_analisis_acciones_institucional(payload)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=status.HTTP_502_BAD_GATEWAY)

        respuesta = {
            'filtro': payload['filtro'],
            'generado_en': timezone.now(),
            'resumen': analisis['resumen'],
            'acciones': analisis['acciones'],
        }
        return Response(SerializadorAnalisisAccionesInstitucional(respuesta).data)
