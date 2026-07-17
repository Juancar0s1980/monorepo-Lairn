"""
Vista de sugerencia de objetivos con IA, para el rol Docente.

Expone `POST /cursos/<curso_id>/objetivos/sugerir/`: genera borradores de
objetivos de aprendizaje a partir del nombre y la descripción del curso,
pasando los objetivos ya existentes para que las sugerencias los complementen
en vez de repetirlos.

Importante: NO guarda nada en la base de datos. Devuelve solo la lista de
sugerencias; el docente las revisa en la UI y guarda las que acepte mediante
el POST normal de la colección de objetivos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, ObjetivoCurso
from apps.motor_adaptativo.services.agente_ia import sugerir_objetivos


@extend_schema(
    tags=['Objetivos'],
    summary='Sugerir objetivos con IA',
    description=(
        'Genera sugerencias de objetivos de aprendizaje para el curso usando IA, '
        'a partir de su nombre y descripción. No guarda nada: el docente decide '
        'cuáles aceptar y las crea con el POST de objetivos.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    request=None,
    responses={
        200: inline_serializer(
            name='RespuestaSugerirObjetivos',
            fields={'sugerencias': drf_serializers.ListField(child=drf_serializers.CharField())},
        ),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
        502: OpenApiResponse(description='La IA no produjo sugerencias válidas'),
    },
)
class VistaSugerirObjetivos(APIView):
    permission_classes = [EsDocente]

    # Genera borradores de objetivos para el curso del docente autenticado.
    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        existentes = list(
            ObjetivoCurso.objects.filter(curso=curso).values_list('descripcion', flat=True)
        )

        try:
            sugerencias = sugerir_objetivos(
                nombre_curso=curso.nombre,
                descripcion_curso=curso.descripcion,
                existentes=existentes,
            )
        except ValueError as e:
            return Response(
                {'detalle': f'No se pudieron generar sugerencias: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'sugerencias': sugerencias})
