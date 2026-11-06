"""
Vista del ranking docente de un curso Saber Pro (HU-23).

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/ranking/` con filtros
opcionales `?simulacro_id=` y `?area_id=`.

- Solo el docente propietario del curso puede consultarlo.
- Sin `simulacro_id` compara todo el curso (área): promedia el mejor intento de
  cada simulacro por estudiante para no premiar la cantidad de repeticiones.
- Con `simulacro_id` usa el mejor intento elegible de cada estudiante en ese
  simulacro.
- El listado es nominal (nombre y correo) porque el docente lo usa con fines
  pedagógicos (HU-23.1/23.2). El estudiante nunca recibe este contrato.
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro
from apps.saber_pro.serializers.serializador_comparacion_saber_pro import (
    SerializadorRankingCurso,
)
from apps.saber_pro.services.comparaciones import (
    AreaNoCorrespondeError,
    CursoNoEncontradoError,
    SimulacroNoEncontradoError,
    construir_ranking,
    obtener_curso_docente,
    resolver_simulacro,
    validar_area,
)
from core.permissions.permisos_rol import EsDocente


def _entero_opcional(valor, nombre):
    """Convierte un query param opcional a entero, con error claro si es inválido."""
    if valor in (None, ''):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'El parámetro {nombre} debe ser un número entero.')


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Consultar el ranking de un curso Saber Pro',
    description=(
        'Retorna el listado nominal ordenado de los estudiantes del curso con su '
        'posición, puntaje 0-100 y calificación 0.0-5.0. Puede filtrarse por '
        'simulacro o por área (el área siempre es la del curso). Solo el docente '
        'propietario del curso puede consultarlo.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por un simulacro del curso'),
        OpenApiParameter('area_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Valida el área del curso'),
    ],
    responses={
        200: SerializadorRankingCurso,
        400: OpenApiResponse(description='Parámetro o área inválida'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
    },
)
class VistaRankingCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            area_id = _entero_opcional(request.query_params.get('area_id'), 'area_id')
            simulacro_id = _entero_opcional(
                request.query_params.get('simulacro_id'),
                'simulacro_id',
            )
            curso = obtener_curso_docente(request.user, curso_id)
            validar_area(curso, area_id)
            simulacro = resolver_simulacro(curso, simulacro_id)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except AreaNoCorrespondeError as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_400_BAD_REQUEST)
        except (CursoNoEncontradoError, SimulacroNoEncontradoError) as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_404_NOT_FOUND)

        filas = construir_ranking(curso, simulacro)
        payload = {
            'curso': curso,
            'filtro': {
                'tipo': 'simulacro' if simulacro is not None else 'area',
                'simulacro': simulacro,
            },
            'total_estudiantes': len(filas),
            'total_inscritos': InscripcionCursoSaberPro.objects.filter(curso=curso).count(),
            'ranking': filas,
        }
        return Response(SerializadorRankingCurso(payload).data)
