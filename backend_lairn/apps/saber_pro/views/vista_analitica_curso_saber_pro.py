"""
Vista de analítica de resultados de un curso Saber Pro para el docente (HU-24).

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/analitica/` con filtros
opcionales `?simulacro_id=`, `?periodo=AAAA-N`, `?competencia_id=`,
`?afirmacion_id=` y `?parte=` (en Inglés), además de `?area_id=` para validar
el área del curso.

- Solo el docente propietario del curso puede consultarlo (HU-24.1.5).
- Devuelve resultados individuales y agregados del curso, la distribución de
  calificaciones y el desempeño por área, competencia y afirmación (o por parte
  del examen en Inglés).
- El filtro por competencia/afirmación refina los desgloses; el resumen y los
  resultados individuales se mantienen sobre el curso/periodo elegido.
- El periodo académico se deriva de la fecha de finalización de cada intento.
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_analitica_saber_pro import (
    SerializadorAnaliticaCurso,
)
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
    summary='Consultar la analítica de un curso Saber Pro',
    description=(
        'Retorna los resultados individuales y agregados del curso, la '
        'distribución de calificaciones y el desempeño por área, competencia y '
        'afirmación. Filtra por simulacro y periodo académico (AAAA-1/AAAA-2); '
        'los filtros de competencia/afirmación refinan los desgloses y en '
        'Inglés el filtro por parte (1 a 7) hace lo propio. Solo el docente '
        'propietario del curso puede consultarlo.'
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
        200: SerializadorAnaliticaCurso,
        400: OpenApiResponse(description='Parámetro, área o criterio inválido'),
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
    },
)
class VistaAnaliticaCursoSaberPro(APIView):
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

        return Response(SerializadorAnaliticaCurso(payload).data)
