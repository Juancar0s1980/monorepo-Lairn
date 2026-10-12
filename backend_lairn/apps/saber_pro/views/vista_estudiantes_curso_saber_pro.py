"""
Vista del listado de estudiantes inscritos a un curso Saber Pro (HU-17.5).

Expone `GET /docente/cursos/<curso_id>/estudiantes/`: devuelve las inscripciones
del curso del docente autenticado con el nombre completo del estudiante, su email
y la fecha de ingreso. El recurso efectivamente manipulable es
`InscripcionCursoSaberPro`; el borrado de una inscripción no forma parte de la
HU-17 (llega con la gestión de estudiantes y la inscripción plena de la HU-18).

El curso se filtra por `docente=request.user`: si no existe o pertenece a otro
docente, la respuesta es 404 para no revelar la existencia de cursos ajenos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models import CursoSaberPro, InscripcionCursoSaberPro
from apps.saber_pro.serializers import SerializadorEstudianteInscrito


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Estudiantes inscritos a un curso Saber Pro',
    description='Retorna la lista de estudiantes inscritos a un curso del docente autenticado, con su nombre, email y fecha de ingreso (HU-17.5).',
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
    ],
    responses={
        200: SerializadorEstudianteInscrito(many=True),
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaEstudiantesCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    # Lista las inscripciones del curso del docente con los datos del estudiante asociado.
    def get(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        inscripciones = InscripcionCursoSaberPro.objects.filter(curso=curso) \
            .select_related('estudiante')
        serializador = SerializadorEstudianteInscrito(inscripciones, many=True)
        return Response(serializador.data)