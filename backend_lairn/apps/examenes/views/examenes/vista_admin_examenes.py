"""
Vista de supervisión global de exámenes, para el rol Administrador.

Expone el endpoint `/administracion/examenes/` que lista todos los exámenes
del sistema (de cualquier docente y curso), a diferencia de
`vista_crear_examen` que solo lista los del docente autenticado. Cada examen
se enriquece con el nombre del curso y del docente para que el administrador
pueda auditar la configuración académica sin navegar curso por curso.

Admite el filtro opcional `?curso_id=` para acotar el listado a un curso.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import serializers as drf_serializers
from core.permissions.permisos_rol import EsAdministrador
from apps.examenes.models import Examen


@extend_schema(
    tags=['Exámenes'],
    summary='Listar todos los exámenes (Administrador)',
    description='Retorna todos los exámenes del sistema con su curso y docente. Solo accesible para el Administrador.',
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra por curso'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaExamenAdmin',
            fields={
                'id': drf_serializers.IntegerField(),
                'titulo': drf_serializers.CharField(),
                'tema': drf_serializers.CharField(),
                'modo': drf_serializers.CharField(),
                'num_preguntas': drf_serializers.IntegerField(),
                'tiempo': drf_serializers.IntegerField(),
                'creado_en': drf_serializers.DateTimeField(),
                'curso': inline_serializer(
                    name='CursoDeExamenAdmin',
                    fields={
                        'id': drf_serializers.IntegerField(),
                        'nombre': drf_serializers.CharField(),
                        'codigo': drf_serializers.CharField(),
                    },
                ),
                'docente': inline_serializer(
                    name='DocenteDeExamenAdmin',
                    fields={
                        'nombre': drf_serializers.CharField(),
                        'email': drf_serializers.EmailField(),
                    },
                ),
            },
            many=True,
        ),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaAdminExamenes(APIView):
    permission_classes = [EsAdministrador]

    # Lista todos los exámenes del sistema, opcionalmente filtrados por curso.
    def get(self, request):
        examenes = Examen.objects.select_related('curso', 'curso__docente').order_by('-creado_en')

        curso_id = request.query_params.get('curso_id')
        if curso_id:
            examenes = examenes.filter(curso_id=curso_id)

        data = [
            {
                'id': examen.id,
                'titulo': examen.titulo,
                'tema': examen.tema,
                'modo': examen.modo,
                'num_preguntas': examen.num_preguntas,
                'tiempo': examen.tiempo,
                'creado_en': examen.creado_en,
                'curso': {
                    'id': examen.curso.id,
                    'nombre': examen.curso.nombre,
                    'codigo': examen.curso.codigo,
                },
                'docente': {
                    'nombre': f"{examen.curso.docente.first_name} {examen.curso.docente.first_last_name}".strip(),
                    'email': examen.curso.docente.email,
                },
            }
            for examen in examenes
        ]
        return Response(data)
