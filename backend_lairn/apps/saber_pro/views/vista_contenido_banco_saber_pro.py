"""
Vista del banco de contenido de un curso Saber Pro, para el rol Docente (HU-20.3).

Expone `GET /docente/cursos/<curso_id>/contenido/`: lista el banco del docente
para el área del curso (contenido generado con IA). Soporta filtros por `estado`
(pendiente/aprobado), `competencia_id`, `afirmacion_id`, `evidencia_id` y `parte`
(Inglés). Así el frontend organiza la revisión por pestañas y con filtros más
precisos para acelerar la aprobación.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.evidencia_saber_pro import EvidenciaSaberPro
from apps.saber_pro.serializers import SerializadorContenidoBanco


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Listar el banco de contenido de un curso',
    description=(
        'Devuelve el contenido del banco del docente para el área del curso. '
        'Permite filtrar por estado (pendiente/aprobado), por jerarquía '
        '(competencia/afirmación/evidencia) o por parte en Inglés para facilitar la '
        'revisión y aprobación (HU-20).'
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
        OpenApiParameter(
            name='competencia_id',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filtra por competencia del área.',
        ),
        OpenApiParameter(
            name='afirmacion_id',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filtra por afirmación de la competencia.',
        ),
        OpenApiParameter(
            name='evidencia_id',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filtra por evidencia de la afirmación.',
        ),
        OpenApiParameter(
            name='parte',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte (1-7) en el área de Inglés.',
        ),
    ],
    responses={
        200: SerializadorContenidoBanco(many=True),
        400: OpenApiResponse(description='Filtros inválidos'),
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

        competencia_id = request.query_params.get('competencia_id')
        if competencia_id:
            try:
                competencia_id_int = int(competencia_id)
            except (TypeError, ValueError):
                return Response({'competencia_id': ['Debe ser un número entero.']}, status=status.HTTP_400_BAD_REQUEST)
            if not CompetenciaSaberPro.objects.filter(id=competencia_id_int, area=curso.area).exists():
                return Response({'competencia_id': ['La competencia no pertenece al área del curso.']}, status=status.HTTP_400_BAD_REQUEST)
            contenidos = contenidos.filter(competencia_id=competencia_id_int)

        afirmacion_id = request.query_params.get('afirmacion_id')
        if afirmacion_id:
            try:
                afirmacion_id_int = int(afirmacion_id)
            except (TypeError, ValueError):
                return Response({'afirmacion_id': ['Debe ser un número entero.']}, status=status.HTTP_400_BAD_REQUEST)
            afirmacion = AfirmacionSaberPro.objects.filter(id=afirmacion_id_int).select_related('competencia').first()
            if not afirmacion or afirmacion.competencia.area_id != curso.area_id:
                return Response({'afirmacion_id': ['La afirmación no pertenece al área del curso.']}, status=status.HTTP_400_BAD_REQUEST)
            contenidos = contenidos.filter(afirmacion_id=afirmacion_id_int)

        evidencia_id = request.query_params.get('evidencia_id')
        if evidencia_id:
            try:
                evidencia_id_int = int(evidencia_id)
            except (TypeError, ValueError):
                return Response({'evidencia_id': ['Debe ser un número entero.']}, status=status.HTTP_400_BAD_REQUEST)
            evidencia = EvidenciaSaberPro.objects.filter(id=evidencia_id_int).select_related('afirmacion__competencia').first()
            if not evidencia or evidencia.afirmacion.competencia.area_id != curso.area_id:
                return Response({'evidencia_id': ['La evidencia no pertenece al área del curso.']}, status=status.HTTP_400_BAD_REQUEST)
            contenidos = contenidos.filter(evidencia_id=evidencia_id_int)

        parte = request.query_params.get('parte')
        if parte:
            try:
                parte_int = int(parte)
            except (TypeError, ValueError):
                return Response({'parte': ['Debe ser un número entero.']}, status=status.HTTP_400_BAD_REQUEST)
            if parte_int < 1 or parte_int > 7:
                return Response({'parte': ['La parte debe estar entre 1 y 7.']}, status=status.HTTP_400_BAD_REQUEST)
            contenidos = contenidos.filter(parte=parte_int)

        return Response(SerializadorContenidoBanco(contenidos, many=True).data)