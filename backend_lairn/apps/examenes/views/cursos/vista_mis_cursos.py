"""
Vista de consulta de cursos inscritos para el rol Estudiante.

Expone el endpoint `/mis-cursos/` que lista los cursos en los que el
estudiante autenticado está inscrito.

A diferencia de la vista del docente, el listado no se construye filtrando
`Curso` directamente sino partiendo de `Inscripcion`, que es la fuente de
verdad sobre la relación estudiante-curso. Se usa `select_related` para
traer en la misma query el curso y su docente, de modo que el serializer
(`SerializadorCursoEstudiante`) pueda exponer el nombre del docente sin
generar consultas N+1.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.examenes.serializers import SerializadorCursoEstudiante


@extend_schema(
    tags=['Cursos'],
    summary='Mis cursos inscritos',
    description='Retorna todos los cursos en los que el estudiante autenticado está inscrito.',
    responses={
        200: SerializadorCursoEstudiante(many=True),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
    },
)
class VistaMisCursos(APIView):
    permission_classes = [EsEstudiante]

    # Lista los cursos en los que el estudiante autenticado posee una inscripción activa.
    def get(self, request):
        inscripciones = Inscripcion.objects.filter(
            estudiante=request.user
        ).select_related('curso__docente')
        cursos = [i.curso for i in inscripciones]
        serializador = SerializadorCursoEstudiante(cursos, many=True)
        return Response(serializador.data)
