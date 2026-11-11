"""
Vista de opciones de filtro del desempeño del estudiante Saber Pro (HU-23).

Expone `GET /api/saber-pro/estudiante/desempeno/opciones/`: los cursos
inscritos donde el estudiante tiene al menos un intento calificado y, dentro de
cada curso, solo los simulacros que presentó y ya cuentan para la comparación.

Es la base de los filtros de "Mi desempeño": el estudiante nunca puede elegir
un curso o simulacro sin resultados propios, así la vista siempre arranca sobre
una combinación comparable. No revela datos de otros estudiantes.
"""

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.serializers.serializador_comparacion_saber_pro import (
    SerializadorOpcionCursoDesempeno,
)
from apps.saber_pro.services.comparaciones import opciones_desempeno_estudiante
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Cursos y simulacros comparables de mi desempeño',
    description=(
        'Lista los cursos inscritos donde el estudiante autenticado tiene '
        'resultados calificados y, por cada curso, los simulacros que presentó '
        '(solo intentos finalizados y calificados). Base de los filtros de "Mi '
        'desempeño": no incluye combinaciones sin resultados propios ni datos '
        'de otros estudiantes.'
    ),
    responses={
        200: SerializadorOpcionCursoDesempeno(many=True),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
    },
)
class VistaOpcionesDesempenoEstudianteSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        opciones = opciones_desempeno_estudiante(request.user)
        return Response(SerializadorOpcionCursoDesempeno(opciones, many=True).data)
