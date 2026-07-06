"""
Vista de auto-inscripción a un curso para el rol Estudiante.

Expone el endpoint `/inscribirse/` que recibe el código único de 8 caracteres
del curso y crea la `Inscripcion` correspondiente para el estudiante autenticado.

Se usa código en lugar de `curso_id` porque el flujo está diseñado para que
el docente comparta un identificador corto y opaco con sus estudiantes, sin
exponer el id interno ni listar cursos públicos. La vista rechaza inscripciones
duplicadas explícitamente para mantener la unicidad de la relación
estudiante-curso.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Curso, Inscripcion
from apps.examenes.serializers import SerializadorInscribirse, SerializadorInscripcion


@extend_schema(
    tags=['Cursos'],
    summary='Unirse a un curso',
    description=(
        'El estudiante ingresa el código del curso (8 caracteres) para inscribirse. '
        'Si el código no existe o ya está inscrito, retorna un error.'
    ),
    request=SerializadorInscribirse,
    examples=[
        OpenApiExample(
            name='Inscribirse con codigo',
            value={'codigo': 'AB3X9KLM'},
            request_only=True,
        ),
    ],
    responses={
        201: SerializadorInscripcion,
        400: OpenApiResponse(description='Código inválido o estudiante ya inscrito'),
        403: OpenApiResponse(description='Solo los estudiantes pueden inscribirse'),
    },
)
class VistaInscribirse(APIView):
    permission_classes = [EsEstudiante]

    # Inscribe al estudiante autenticado en el curso identificado por el código recibido, rechazando duplicados.
    def post(self, request):
        serializador = SerializadorInscribirse(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        curso = Curso.objects.get(codigo=serializador.validated_data['codigo'])

        if Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'Ya estás inscrito en este curso.'}, status=status.HTTP_400_BAD_REQUEST)

        inscripcion = Inscripcion.objects.create(estudiante=request.user, curso=curso)
        return Response(SerializadorInscripcion(inscripcion).data, status=status.HTTP_201_CREATED)
