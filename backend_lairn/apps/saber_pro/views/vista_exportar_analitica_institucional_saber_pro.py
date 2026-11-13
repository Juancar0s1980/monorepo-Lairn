"""
Exportación `.xlsx` de la analítica institucional Saber Pro (HU-24.6).

Expone `GET /api/saber-pro/institucional/analitica/exportar/` con los mismos
filtros de la consulta: `?curso_id=`, `?programa_id=`, `?area_id=`,
`?competencia_id=`, `?afirmacion_id=`, `?parte=` (Inglés) y `?periodo=AAAA-N`.
El archivo es agregado y no incluye resultados individuales (HU-24.4.6); el
análisis de acciones con IA se incluye en la hoja "Resumen" (HU-24.7) y, si la
IA falla, la descarga continúa con una nota informativa.
"""

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
from apps.saber_pro.services.exportar_analitica import (
    a_excel_analitica_institucional,
)
from apps.saber_pro.views.parametros_analitica import (
    parametros_analitica_institucional,
)
from core.permissions.permisos_rol import EsLectorAnalitica

CONTENT_TYPE_XLSX = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


@extend_schema(
    tags=['Saber Pro - Institucional'],
    summary='Exportar en Excel la analítica académica institucional de Saber Pro',
    description=(
        'Genera un libro .xlsx con los indicadores consolidados, desgloses y '
        'comparativas por curso, carrera y periodo, con los filtros aplicados '
        '(incluida la parte del examen de Inglés). No incluye resultados '
        'individuales de estudiantes. El análisis de acciones generado con IA '
        'se incluye al final de la hoja "Resumen" con el aviso de que es '
        'automático y puede equivocarse; si la IA falla, la exportación '
        'continúa con una nota informativa.'
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
        200: OpenApiResponse(description='Libro Excel de la analítica institucional'),
        400: OpenApiResponse(description='Parámetro, área o criterio inválido'),
        404: OpenApiResponse(description='Curso o programa no encontrado'),
    },
)
class VistaExportarAnaliticaInstitucionalSaberPro(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
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

        # El Excel incluye el análisis de acciones con IA con los mismos
        # filtros, dentro de la hoja "Resumen". Si la IA falla (o no hay
        # intentos elegibles) la exportación continúa y esa sección lleva una
        # nota informativa en vez del análisis.
        analisis = None
        if payload['resumen']['total_intentos'] > 0:
            try:
                analisis = generar_analisis_acciones_institucional(payload)
            except ValueError:
                analisis = None

        respuesta = HttpResponse(
            a_excel_analitica_institucional(payload, analisis),
            content_type=CONTENT_TYPE_XLSX,
        )
        nombre = f'analitica_institucional_{timezone.localdate():%Y%m%d}.xlsx'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta
