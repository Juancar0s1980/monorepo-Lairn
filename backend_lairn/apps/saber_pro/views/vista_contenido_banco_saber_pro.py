"""
Vista del banco de contenido de un curso Saber Pro, para el rol Docente (HU-20.3).

Expone `GET /docente/cursos/<curso_id>/contenido/`: lista el banco del docente
para el área del curso (contenido generado con IA), filtrando por `estado`
cuando se envía el query param (`pendiente` o `aprobado`). Así el frontend
arma las pestañas de revisión y de contenido aprobado sin endpoints extra.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorContenidoBanco


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Listar el banco de contenido de un curso',
    description=(
        'Devuelve el contenido del banco del docente para el área del curso. El query '
        'param "estado" permite ver solo el contenido pendiente (cola de revisión) o el '
        'aprobado; sin él se devuelve todo.'
    ),
    parameters=[
        OpenApiParameter(
            name='estado',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=['pendiente', 'aprobado'],
            description='Filtra el banco por estado de revisión.',
        ),
    ],
    responses={
        200: SerializadorContenidoBanco(many=True),
        404: OpenApiResponse(description='Curso Saber Pro no encontrado'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
    },
)
class VistaContenidoBancoSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.select_related('area').get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso Saber Pro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        contenidos = ContenidoBancoSaberPro.objects.filter(
            docente=request.user,
            area=curso.area,
        ).select_related('area', 'competencia', 'afirmacion', 'evidencia')

        estado = request.query_params.get('estado')
        if estado in ('pendiente', 'aprobado'):
            contenidos = contenidos.filter(estado=estado)

        return Response(SerializadorContenidoBanco(contenidos, many=True).data)