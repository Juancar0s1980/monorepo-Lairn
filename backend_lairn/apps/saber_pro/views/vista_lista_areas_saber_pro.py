"""
Vista del catálogo de áreas Saber Pro.

Expone `GET /areas/`: devuelve las áreas oficiales del examen (sembradas con
`seed_saber_pro`). El docente las consume para crear un curso (HU-17.1) sin
depender de una lista hardcodeada en el frontend, y las épicas siguientes
(HU-19/20/24) las reutilizarán para simulacros, contenido y analítica.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsDocente, EsEstudiante
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.serializers import SerializadorAreaSaberPro


@extend_schema(
    tags=['Saber Pro'],
    summary='Listar áreas de Saber Pro',
    description='Devuelve el catálogo de áreas oficiales del examen, ordenado como se muestra en la interfaz (HU-17.1).',
    responses={
        200: SerializadorAreaSaberPro(many=True),
        403: OpenApiResponse(description='Solo Docentes y Estudiantes pueden acceder al módulo Saber Pro'),
    },
)
class VistaListaAreasSaberPro(APIView):
    permission_classes = [EsDocente | EsEstudiante]

    def get(self, request):
        areas = AreaSaberPro.objects.all()
        return Response(SerializadorAreaSaberPro(areas, many=True).data)