"""
Vista colección de cursos Saber Pro para el rol Docente (HU-17).

Expone el endpoint `/docente/cursos/` con dos operaciones:
- POST: crea un curso de preparación. El docente solo envía área, nombre y
  descripción (HU-17.1); el sistema genera automáticamente un código único
  (HU-17.2) que NO aparece en el request y que se devuelve en la respuesta.
- GET: lista los cursos Saber Pro creados por el docente autenticado.

Se modela como una única vista de colección porque ambas operaciones comparten
permiso (`EsDocente`), scope (los cursos del docente) y serializer. El detalle
(retrieve/update/delete) vive en `vista_detalle_curso_saber_pro` para mantener
la separación REST entre colección y recurso individual.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorCursoSaberPro
from apps.saber_pro.services.codigos import generar_codigo_unico


@extend_schema_view(
    get=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Listar mis cursos Saber Pro',
        description='Retorna todos los cursos Saber Pro creados por el docente autenticado, con su área y código de acceso vigente.',
        responses={
            200: SerializadorCursoSaberPro(many=True),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        },
    ),
    post=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Crear curso Saber Pro',
        description=(
            'Crea un curso de preparación indicando el área, el nombre y una descripción. '
            'El sistema genera automáticamente un código de acceso único que el docente '
            'comparte con sus estudiantes; el docente nunca lo digita ni lo define.'
        ),
        request=SerializadorCursoSaberPro,
        examples=[
            OpenApiExample(
                name='Curso de preparación',
                value={
                    'nombre': 'Preparación Inglés B1',
                    'descripcion': 'Refuerzo de las 7 partes del examen',
                    'area_id': 5,
                },
                request_only=True,
            ),
        ],
        responses={
            201: SerializadorCursoSaberPro,
            400: OpenApiResponse(description='Datos inválidos (el área es obligatoria)'),
            403: OpenApiResponse(description='Solo los docentes pueden crear cursos'),
        },
    ),
)
class VistaCrearCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    # Crea un curso de preparación asignando el docente y un código único automático (HU-17.1/17.2).
    def post(self, request):
        serializador = SerializadorCursoSaberPro(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        serializador.save(
            docente=request.user,
            codigo=generar_codigo_unico(),
        )
        return Response(serializador.data, status=status.HTTP_201_CREATED)

    # Lista los cursos de preparación del docente autenticado.
    def get(self, request):
        cursos = CursoSaberPro.objects.filter(docente=request.user).select_related('area')
        serializador = SerializadorCursoSaberPro(cursos, many=True)
        return Response(serializador.data)