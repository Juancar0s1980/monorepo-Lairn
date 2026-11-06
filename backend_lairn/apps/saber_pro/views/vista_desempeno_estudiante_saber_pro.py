"""
Vista del desempeño propio del estudiante Saber Pro (HU-23).

Expone `GET /api/saber-pro/estudiante/desempeno/` con filtros opcionales
`?curso_id=`, `?area_id=` y `?simulacro_id=`.

La respuesta contiene únicamente los agregados del estudiante autenticado y de
su grupo: puntaje, calificación, total de estudiantes con resultados y percentil
(porcentaje de compañeros superados). Nunca incluye nombres, correos ni
posiciones individuales de otros estudiantes (HU-23.4).
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_comparacion_saber_pro import (
    SerializadorDesempenoEstudiante,
)
from apps.saber_pro.services.comparaciones import (
    AreaNoCorrespondeError,
    CursoNoEncontradoError,
    SimulacroNoEncontradoError,
    calcular_desempeno,
    resolver_curso_estudiante,
)
from core.permissions.permisos_rol import EsEstudiante


def _entero_opcional(valor, nombre):
    """Convierte un query param opcional a entero, con error claro si es inválido."""
    if valor in (None, ''):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'El parámetro {nombre} debe ser un número entero.')


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Consultar mi desempeño frente a mi curso Saber Pro',
    description=(
        'Retorna el puntaje y la calificación del estudiante autenticado, el '
        'número de compañeros con resultados y su percentil (porcentaje de '
        'estudiantes superados). No revela nombres, correos ni posiciones de '
        'otros estudiantes.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Curso inscrito a consultar'),
        OpenApiParameter('area_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Área de un curso inscrito'),
        OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Simulacro del curso a consultar'),
    ],
    responses={
        200: SerializadorDesempenoEstudiante,
        400: OpenApiResponse(description='Parámetro o área inválida'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
    },
)
class VistaDesempenoEstudianteSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        try:
            curso, simulacro = resolver_curso_estudiante(
                request.user,
                curso_id=_entero_opcional(request.query_params.get('curso_id'), 'curso_id'),
                area_id=_entero_opcional(request.query_params.get('area_id'), 'area_id'),
                simulacro_id=_entero_opcional(
                    request.query_params.get('simulacro_id'),
                    'simulacro_id',
                ),
            )
        except ValueError as error:
            return Response({'detalle': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except AreaNoCorrespondeError as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_400_BAD_REQUEST)
        except (CursoNoEncontradoError, SimulacroNoEncontradoError) as error:
            return Response({'detalle': error.mensaje}, status=status.HTTP_404_NOT_FOUND)

        desempeno = calcular_desempeno(request.user, curso, simulacro)
        payload = {
            'curso': curso,
            'filtro': {
                'tipo': 'simulacro' if simulacro is not None else 'area',
                'simulacro': simulacro,
            },
            **desempeno,
        }
        return Response(SerializadorDesempenoEstudiante(payload).data)
