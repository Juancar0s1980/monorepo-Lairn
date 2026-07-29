"""
Vista de generación de temas de estudio con IA, para el rol Docente.

Expone `POST /cursos/<curso_id>/campo-estudio/temas/generar/`: genera temas
de estudio anclados al curso (nombre, descripción y objetivos si existen) y
los persiste como `pendiente`. A diferencia de `VistaSugerirObjetivos`, esta
vista SÍ guarda: el docente los revisa después en la cola, no en un modal
inmediato tras generar.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, ObjetivoCurso
from apps.campo_estudio.models import TemaEstudio
from apps.campo_estudio.serializers import SerializadorTemaEstudio
from apps.campo_estudio.services.agente_estudio import generar_temas_estudio


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Generar temas de estudio con IA',
    description=(
        'Genera borradores de temas de estudio para el curso usando IA y los '
        'guarda como "pendiente". El docente los aprueba o elimina después desde '
        'la cola de revisión (GET de la misma colección).'
    ),
    request=None,
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        201: SerializadorTemaEstudio(many=True),
        404: OpenApiResponse(description='Curso no encontrado'),
        502: OpenApiResponse(description='La IA no produjo temas válidos'),
    },
)
class VistaGenerarTemasEstudio(APIView):
    permission_classes = [EsDocente]

    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        objetivos = list(ObjetivoCurso.objects.filter(curso=curso).values_list('descripcion', flat=True))
        existentes = list(TemaEstudio.objects.filter(curso=curso).values_list('titulo', flat=True))

        try:
            borradores = generar_temas_estudio(
                nombre_curso=curso.nombre,
                descripcion_curso=curso.descripcion,
                objetivos=objetivos,
                existentes=existentes,
            )
        except ValueError as e:
            return Response(
                {'detalle': f'No se pudieron generar temas de estudio: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        creados = [
            TemaEstudio.objects.create(curso=curso, titulo=b['titulo'], contenido=b['contenido'])
            for b in borradores
        ]
        serializador = SerializadorTemaEstudio(creados, many=True)
        return Response(serializador.data, status=status.HTTP_201_CREATED)
