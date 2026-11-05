"""
Vista colección de simulacros de un curso Saber Pro (HU-19.1).

Expone `GET/POST /api/saber-pro/docente/cursos/<curso_id>/simulacros/`.

- GET: lista los simulacros del curso del docente autenticado.
- POST: crea un simulacro heredando el área del curso, con 40 preguntas por
  defecto y 60 minutos de tiempo límite. El sistema selecciona aleatoriamente
  contenido aprobado del banco (HU-19.2/19.3/20.4).

Toda la operación se ejecuta en una transacción: si el banco no alcanza para la
distribución pedida, no queda un simulacro parcial y se devuelve un 400 con el
detalle de las preguntas faltantes.
"""

from django.db import transaction
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers import (
    SerializadorCrearEditarSimulacro,
    SerializadorSimulacro,
)
from apps.saber_pro.services.simulacros import ContenidoInsuficienteError
from core.permissions.permisos_rol import EsDocente


def simulacros_del_curso(curso):
    """QuerySet con las relaciones que consume `SerializadorSimulacro`."""
    return (
        Simulacro.objects.filter(curso=curso)
        .select_related('curso__area')
        .prefetch_related(
            'distribuciones__competencia',
            'distribuciones__afirmacion',
            'preguntas_asignadas__contenido',
        )
    )


@extend_schema_view(
    get=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Listar simulacros de un curso Saber Pro',
        description='Retorna los simulacros del curso del docente autenticado, con su distribución y total de preguntas asignadas (HU-19.1).',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            200: SerializadorSimulacro(many=True),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    post=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Crear simulacro en un curso Saber Pro',
        description=(
            'Crea un simulacro en el curso heredando su área. Si no se indica '
            '`num_preguntas` se usan 40. En áreas estructuradas, omitir '
            '`distribuciones` aplica la estructura oficial completa y reparte las '
            'preguntas según sus porcentajes (competencias en Razonamiento '
            'Cuantitativo/Competencias Ciudadanas y afirmaciones en Lectura '
            'Crítica). Si se envían criterios, sus cantidades deben coincidir con '
            'ese reparto. En Inglés el total siempre es 45 y se asignan las 7 '
            'partes completas, por lo que las distribuciones se ignoran '
            '(HU-19.1-19.3).'
        ),
        request=SerializadorCrearEditarSimulacro,
        examples=[
            OpenApiExample(
                name='Simulacro con estructura oficial completa',
                value={
                    'titulo': 'Simulacro diagnóstico',
                    'descripcion': 'Cobertura oficial del área',
                    'num_preguntas': 40,
                    'tiempo_limite_minutos': 60,
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Simulacro con subconjunto de criterios',
                value={
                    'titulo': 'Simulacro de refuerzo',
                    'num_preguntas': 20,
                    'tiempo_limite_minutos': 40,
                    'distribuciones': [
                        {'competencia_id': 1},
                        {'competencia_id': 2},
                    ],
                },
                description=(
                    'Las cantidades se omiten: el backend reparte las 20 preguntas '
                    'según los porcentajes de los criterios enviados.'
                ),
                request_only=True,
            ),
        ],
        responses={
            201: SerializadorSimulacro,
            400: OpenApiResponse(description='Datos inválidos o banco aprobado insuficiente'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
)
class VistaSimulacrosCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        curso = self._obtener_curso(request, curso_id)
        if isinstance(curso, Response):
            return curso

        serializador = SerializadorSimulacro(simulacros_del_curso(curso), many=True)
        return Response(serializador.data)

    def post(self, request, curso_id):
        curso = self._obtener_curso(request, curso_id)
        if isinstance(curso, Response):
            return curso

        serializador = SerializadorCrearEditarSimulacro(
            data=request.data,
            context={'curso': curso},
        )
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                simulacro = serializador.save()
        except ContenidoInsuficienteError as error:
            return Response(
                {'detalle': error.mensaje, 'errores': error.detalles},
                status=status.HTTP_400_BAD_REQUEST,
            )

        simulacro = simulacros_del_curso(curso).get(id=simulacro.id)
        return Response(
            SerializadorSimulacro(simulacro).data,
            status=status.HTTP_201_CREATED,
        )

    def _obtener_curso(self, request, curso_id):
        try:
            return CursoSaberPro.objects.select_related('area').get(
                id=curso_id,
                docente=request.user,
            )
        except CursoSaberPro.DoesNotExist:
            return Response(
                {'detalle': 'Curso no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
