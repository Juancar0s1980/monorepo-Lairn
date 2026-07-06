"""
Vista de gestión de exámenes para el rol Docente.

Expone el endpoint colección `/examenes/` con dos operaciones:
- POST: crea un examen dentro de un curso propio del docente.
- GET: lista todos los exámenes de todos los cursos del docente autenticado.

Se diseña como una única vista de "colección" porque ambas operaciones comparten
el mismo permiso (`EsDocente`), el mismo scope (los exámenes del docente) y el
mismo serializer de gestión (`SerializadorCrearExamen`, que expone el FK `curso`
y todos los parámetros de configuración del examen). Las operaciones de detalle
(retrieve/update/delete sobre un examen específico) viven en una vista aparte
para mantener separadas las responsabilidades de colección y de recurso individual.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, Examen
from apps.examenes.serializers import SerializadorCrearExamen


@extend_schema_view(
    get=extend_schema(
        tags=['Exámenes'],
        summary='Listar mis exámenes',
        description='Retorna todos los exámenes creados en los cursos del docente autenticado.',
        responses={
            200: SerializadorCrearExamen(many=True),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        },
    ),
    post=extend_schema(
        tags=['Exámenes'],
        summary='Crear examen',
        description=(
            'Crea un examen dentro de un curso. El agente de IA generará las preguntas en tiempo real '
            'cuando el estudiante lo presente.\n\n'
            '**Parámetros clave:**\n'
            '- `num_preguntas`: En modo fijo es el total exacto. En modo maestría es el mínimo garantizado.\n'
            '- `max_intentos`: 0 = ilimitado, 1-10 = número exacto de intentos.\n'
            '- `dificultad_inicial`: 1=Fácil, 2=Medio, 3=Difícil.\n'
            '- `modo`: `fijo` termina al llegar a num_preguntas. `maestria` termina cuando el '
            'estudiante domina todos los conceptos o alcanza max_preguntas.\n'
            '- `es_guiado`: Si es true, el agente genera una explicación del concepto antes de cada pregunta.\n'
            '- `retroalimentacion`: Si es true, el estudiante ve si acertó o falló después de cada respuesta.'
        ),
        request=SerializadorCrearExamen,
        examples=[
            OpenApiExample(
                name='Examen modo fijo',
                value={
                    'curso': 1,
                    'titulo': 'Examen de Derivadas',
                    'tema': 'Derivadas de funciones trigonometricas',
                    'tiempo': 30,
                    'num_preguntas': 10,
                    'retroalimentacion': True,
                    'dificultad_inicial': 1,
                    'max_intentos': 3,
                    'es_guiado': False,
                    'modo': 'fijo',
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Examen modo maestria',
                value={
                    'curso': 1,
                    'titulo': 'Practica de Integrales',
                    'tema': 'Integrales por sustitucion',
                    'tiempo': 60,
                    'num_preguntas': 5,
                    'retroalimentacion': True,
                    'dificultad_inicial': 1,
                    'max_intentos': 0,
                    'es_guiado': True,
                    'modo': 'maestria',
                    'max_preguntas': 25,
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Examen guiado sin limite de intentos',
                value={
                    'curso': 1,
                    'titulo': 'Repaso de Limites',
                    'tema': 'Limites al infinito y limites laterales',
                    'tiempo': 45,
                    'num_preguntas': 8,
                    'retroalimentacion': True,
                    'dificultad_inicial': 2,
                    'max_intentos': 0,
                    'es_guiado': True,
                    'modo': 'fijo',
                },
                request_only=True,
            ),
        ],
        responses={
            201: SerializadorCrearExamen,
            400: OpenApiResponse(description='Datos inválidos o max_preguntas menor que num_preguntas en modo maestría'),
            403: OpenApiResponse(description='Solo los docentes pueden crear exámenes o el curso no le pertenece'),
        },
    ),
)
class VistaCrearExamen(APIView):
    permission_classes = [EsDocente]

    # Crea un examen validando que el curso destino pertenezca al docente autenticado.
    def post(self, request):
        serializador = SerializadorCrearExamen(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        curso = serializador.validated_data['curso']
        if curso.docente != request.user:
            return Response(
                {'detalle': 'No tienes permiso para crear exámenes en este curso.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializador.save()
        return Response(serializador.data, status=status.HTTP_201_CREATED)

    # Lista todos los exámenes pertenecientes a los cursos del docente autenticado.
    def get(self, request):
        cursos_docente = Curso.objects.filter(docente=request.user)
        examenes = Examen.objects.filter(curso__in=cursos_docente)
        serializador = SerializadorCrearExamen(examenes, many=True)
        return Response(serializador.data)
