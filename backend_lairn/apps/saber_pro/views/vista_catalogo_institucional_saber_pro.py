"""
Catálogo de filtros de la analítica institucional Saber Pro (HU-24.3).

Expone `GET /api/saber-pro/institucional/catalogo/` con las áreas, carreras
(programas académicos) y cursos que existen en la institución. La vista
institucional lo usa para poblar sus selectores sin depender de endpoints
restringidos al docente o al gestor académico.

Solo lectura y con el mismo permiso de la analítica institucional
(`EsLectorAnalitica`).
"""

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers.serializador_analitica_saber_pro import (
    SerializadorCatalogoInstitucional,
)
from core.permissions.permisos_rol import EsLectorAnalitica


@extend_schema(
    tags=['Saber Pro - Institucional'],
    summary='Catálogo de filtros de la analítica institucional Saber Pro',
    description=(
        'Devuelve las áreas, carreras (programas académicos) y cursos Saber Pro '
        'disponibles para filtrar y comparar la analítica institucional.'
    ),
    responses={200: SerializadorCatalogoInstitucional},
)
class VistaCatalogoInstitucionalSaberPro(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        payload = {
            'areas': AreaSaberPro.objects.all(),
            'programas': ProgramaAcademico.objects.all(),
            'cursos': CursoSaberPro.objects.select_related('area').order_by('nombre', 'id'),
        }
        return Response(SerializadorCatalogoInstitucional(payload).data)
