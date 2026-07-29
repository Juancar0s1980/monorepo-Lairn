"""
Vista para activar/desactivar el Campo de Estudio de un curso, para el rol
Docente.

Expone `PATCH /cursos/<curso_id>/campo-estudio/activar/` con
`{"habilitado": true|false}`. Se pide el valor explícito (no un toggle
ciego) para que dos clics seguidos del docente sean idempotentes.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Activar/desactivar el Campo de Estudio del curso',
    description=(
        'Enciende o apaga el Campo de Estudio del curso. Apagado por defecto: '
        'mientras esté apagado, ningún estudiante ve temas ni puede preguntar, '
        'aunque existan temas ya aprobados.'
    ),
    request=inline_serializer(name='ActivarCampoEstudio', fields={'habilitado': drf_serializers.BooleanField()}),
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: inline_serializer(name='RespuestaActivarCampoEstudio', fields={'habilitado': drf_serializers.BooleanField()}),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaActivarCampoEstudio(APIView):
    permission_classes = [EsDocente]

    def patch(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        habilitado = request.data.get('habilitado')
        if not isinstance(habilitado, bool):
            return Response({'detalle': '"habilitado" debe ser true o false.'}, status=status.HTTP_400_BAD_REQUEST)

        curso.campo_estudio_habilitado = habilitado
        curso.save(update_fields=['campo_estudio_habilitado'])
        return Response({'habilitado': curso.campo_estudio_habilitado})
