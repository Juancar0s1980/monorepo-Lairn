"""
Vista colección de cursos para el rol Docente.

Expone el endpoint `/cursos/` con dos operaciones:
- POST: crea un nuevo curso, generando automáticamente un código único de 8
  caracteres que el docente comparte con sus estudiantes para la inscripción.
- GET: lista todos los cursos del docente autenticado.

Se modela como una única vista de colección porque ambas operaciones comparten
permiso (`EsDocente`), scope (los cursos del docente) y serializer. Las
operaciones de detalle sobre un curso específico (retrieve/update/delete)
viven en `vista_detalle_curso` para mantener la separación REST entre
colección y recurso individual.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.examenes.serializers import SerializadorCrearCurso


@extend_schema_view(
    get=extend_schema(
        tags=['Cursos'],
        summary='Listar mis cursos',
        description='Retorna todos los cursos creados por el docente autenticado.',
        responses={
            200: SerializadorCrearCurso(many=True),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        },
    ),
    post=extend_schema(
        tags=['Cursos'],
        summary='Crear curso',
        description='Crea un nuevo curso. El sistema genera automáticamente un código único de 8 caracteres que el docente puede compartir con sus estudiantes.',
        request=SerializadorCrearCurso,
        examples=[
            OpenApiExample(
                name='Curso de Calculo',
                value={'nombre': 'Calculo I', 'descripcion': 'Limites, derivadas e integrales'},
                request_only=True,
            ),
            OpenApiExample(
                name='Curso de Algebra',
                value={'nombre': 'Algebra Lineal', 'descripcion': 'Vectores, matrices y transformaciones'},
                request_only=True,
            ),
        ],
        responses={
            201: SerializadorCrearCurso,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='Solo los docentes pueden crear cursos'),
        },
    ),
)
class VistaCrearCurso(APIView):
    permission_classes = [EsDocente]

    # Crea un nuevo curso asociado al docente autenticado.
    def post(self, request):
        serializador = SerializadorCrearCurso(data=request.data)
        if serializador.is_valid():
            serializador.save(docente=request.user)
            return Response(serializador.data, status=status.HTTP_201_CREATED)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Lista todos los cursos pertenecientes al docente autenticado.
    def get(self, request):
        cursos = Curso.objects.filter(docente=request.user)
        serializador = SerializadorCrearCurso(cursos, many=True)
        return Response(serializador.data)
