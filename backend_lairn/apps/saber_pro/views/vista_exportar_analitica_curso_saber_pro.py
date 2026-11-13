"""
Exportación `.xlsx` de la analítica de un curso Saber Pro (HU-24.5).

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/analitica/exportar/` con
los mismos filtros de la consulta: `?simulacro_id=`, `?periodo=AAAA-N`,
`?competencia_id=`, `?afirmacion_id=`, `?parte=` (Inglés) y `?area_id=`. Solo
el docente propietario del curso puede descargar el archivo.
"""

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
from apps.saber_pro.services.exportar_analitica import a_excel_analitica_curso
from apps.saber_pro.views.parametros_analitica import (
    parametros_analitica_curso,
)
from core.permissions.permisos_rol import EsDocente

CONTENT_TYPE_XLSX = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Exportar en Excel la analítica de un curso Saber Pro',
    description=(
        'Genera un libro .xlsx con los mismos datos y filtros de la consulta '
        'de analítica del curso, incluidos los resultados individuales de los '
        'estudiantes y el filtro por parte en Inglés. El análisis de acciones '
        'generado con IA se incluye al final de la primera hoja ("Resumen"), '
        'con el aviso de que es automático y puede equivocarse. Solo el '
        'docente propietario del curso puede descargarlo.'
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
        200: OpenApiResponse(description='Libro Excel de la analítica del curso'),
        400: OpenApiResponse(description='Parámetro, área o criterio inválido'),
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
    },
)
class VistaExportarAnaliticaCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
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

        # El Excel incluye el análisis de acciones con IA con los mismos
        # filtros, dentro de la hoja "Resumen". Si la IA falla (o el curso no
        # tiene intentos elegibles) la exportación continúa y esa sección
        # lleva una nota informativa en vez del análisis.
        analisis = None
        if payload['resumen']['total_intentos'] > 0:
            try:
                analisis = generar_analisis_acciones_curso(payload)
            except ValueError:
                analisis = None

        respuesta = HttpResponse(
            a_excel_analitica_curso(payload, analisis),
            content_type=CONTENT_TYPE_XLSX,
        )
        nombre = f'analitica_curso_{curso_id}_{timezone.localdate():%Y%m%d}.xlsx'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta
