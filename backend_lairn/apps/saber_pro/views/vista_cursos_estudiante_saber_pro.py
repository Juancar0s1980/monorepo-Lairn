"""
Vista de consulta de los cursos Saber Pro del estudiante (HU-18.3).

Expone `GET /api/saber-pro/estudiante/cursos/`: lista las inscripciones del
estudiante autenticado con su curso, para que el panel lo muestre entre sus
cursos de preparación disponibles. Parte de `InscripcionCursoSaberPro` (la
fuente de verdad de la relación estudiante-curso, mismo criterio que
`examenes.vista_mis_cursos`) con `select_related` en el servicio para evitar
consultas N+1. Cada inscripción conserva su `fecha` de ingreso.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.saber_pro.serializers import SerializadorInscripcionCursoSaberPro
from apps.saber_pro.services.inscripciones import obtener_cursos_de_estudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Cursos Saber Pro del estudiante',
    description=(
        'Retorna las inscripciones del estudiante autenticado, cada una con el '
        'curso Saber Pro al que pertenece y su fecha de ingreso (HU-18.3).'
    ),
    responses={
        200: SerializadorInscripcionCursoSaberPro(many=True),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
    },
)
class VistaCursosEstudianteSaberPro(APIView):
    permission_classes = [EsEstudiante]

    # Lista las inscripciones del estudiante autenticado con su curso (HU-18.3).
    def get(self, request):
        inscripciones = obtener_cursos_de_estudiante(request.user)
        serializador = SerializadorInscripcionCursoSaberPro(inscripciones, many=True)
        return Response(serializador.data)