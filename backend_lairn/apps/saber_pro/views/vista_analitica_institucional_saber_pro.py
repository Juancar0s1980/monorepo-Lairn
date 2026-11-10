"""
Vista de analítica académica institucional de Saber Pro (HU-24.3/24.4).

Expone `GET /api/saber-pro/institucional/analitica/` con filtros opcionales
`?curso_id=`, `?programa_id=` (carrera), `?area_id=`, `?competencia_id=`,
`?afirmacion_id=`, `?parte=` (Inglés) y `?periodo=AAAA-N`.

- La consulta es consolidada: no expone resultados individuales de estudiantes
  (HU-24.4.6), solo indicadores, desgloses y comparativas.
- Devuelve el desempeño por área, competencia y afirmación (o por parte del
  examen en Inglés), la distribución de calificaciones y la comparación entre
  cursos, carreras y periodos académicos (HU-24.3.4).
- El acceso se restringe con `EsLectorAnalitica` (Coordinador, Vicerrector y
  Administrador en solo lectura), el mismo permiso de la analítica
  institucional del resto del sistema.
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_analitica_saber_pro import (
    SerializadorAnaliticaInstitucional,
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
from core.permissions.permisos_rol import EsLectorAnalitica


@extend_schema(
    tags=['Saber Pro - Institucional'],
    summary='Consultar la analítica académica institucional de Saber Pro',
    description=(
        'Retorna indicadores consolidados de todos los cursos Saber Pro, con '
        'desgloses por área, competencia y afirmación (o por parte en Inglés) '
        'y comparativas por curso, carrera y periodo. No expone resultados '
        'individuales de estudiantes. Filtra por curso, carrera, área, criterio '
        'y periodo académico (AAAA-1/AAAA-2).'
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
        200: SerializadorAnaliticaInstitucional,
        400: OpenApiResponse(description='Parámetro, área o criterio inválido'),
        404: OpenApiResponse(description='Curso o programa no encontrado'),
    },
)
class VistaAnaliticaInstitucionalSaberPro(APIView):
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

        return Response(SerializadorAnaliticaInstitucional(payload).data)
