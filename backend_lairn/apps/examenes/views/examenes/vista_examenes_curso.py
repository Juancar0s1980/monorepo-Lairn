"""
Vista de consulta de exámenes para el rol Estudiante.

Expone el endpoint anidado `/mis-cursos/<curso_id>/examenes/` que lista los
exámenes disponibles dentro de un curso específico en el que el estudiante
está inscrito.

Es una vista separada de la de gestión del docente porque:
- El permiso es distinto (`EsEstudiante` vs `EsDocente`).
- La validación de acceso es distinta: en lugar de ownership del curso se
  exige una inscripción activa del estudiante en el curso.
- El scope es un único curso (anidado en la URL), no el conjunto global de
  exámenes del usuario.
- El serializer (`SerializadorExamen`) omite el FK `curso` y los campos de
  gestión que no son relevantes para el consumidor del examen.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Examen, Inscripcion
from apps.examenes.serializers import SerializadorExamen


@extend_schema(
    tags=['Exámenes'],
    summary='Exámenes de un curso (estudiante)',
    description=(
        'Retorna todos los exámenes disponibles en un curso. '
        'El estudiante debe estar inscrito en el curso para poder verlos.'
    ),
    responses={
        200: SerializadorExamen(many=True),
        403: OpenApiResponse(description='No estás inscrito en este curso o no eres estudiante'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaExamenesCurso(APIView):
    permission_classes = [EsEstudiante]

    # Lista los exámenes del curso solicitado validando que el estudiante esté inscrito en él.
    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response(
                {'detalle': 'No estás inscrito en este curso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        examenes = Examen.objects.filter(curso=curso)
        serializador = SerializadorExamen(examenes, many=True)
        return Response(serializador.data)
