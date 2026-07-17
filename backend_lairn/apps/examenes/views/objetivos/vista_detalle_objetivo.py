"""
Vista de detalle de un objetivo de aprendizaje, para el rol Docente.

Expone `/cursos/<curso_id>/objetivos/<objetivo_id>/` con:
- PATCH: edita la descripción u orden del objetivo.
- DELETE: elimina el objetivo. Los exámenes que lo tenían anclado simplemente
  dejan de incluirlo (el M2M se limpia solo); su historial de respuestas no
  se toca porque las respuestas guardan el texto del concepto, no el FK.

El objetivo se busca siempre a través del curso del docente autenticado, de
modo que editar/eliminar objetivos de cursos ajenos responde 404.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import ObjetivoCurso
from apps.examenes.serializers import SerializadorObjetivo


@extend_schema_view(
    patch=extend_schema(
        tags=['Objetivos'],
        summary='Editar objetivo',
        description='Edita la descripción u orden de un objetivo del curso del docente autenticado.',
        request=SerializadorObjetivo,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
            OpenApiParameter('objetivo_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del objetivo'),
        ],
        responses={
            200: SerializadorObjetivo,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
            404: OpenApiResponse(description='Objetivo no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Objetivos'],
        summary='Eliminar objetivo',
        description='Elimina un objetivo del curso. Los exámenes que lo usaban dejan de anclarlo.',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
            OpenApiParameter('objetivo_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del objetivo'),
        ],
        responses={
            204: OpenApiResponse(description='Objetivo eliminado'),
            403: OpenApiResponse(description='Solo los docentes pueden acceder'),
            404: OpenApiResponse(description='Objetivo no encontrado'),
        },
    ),
)
class VistaDetalleObjetivo(APIView):
    permission_classes = [EsDocente]

    def _obtener(self, request, curso_id, objetivo_id):
        return ObjetivoCurso.objects.get(
            id=objetivo_id, curso_id=curso_id, curso__docente=request.user
        )

    # Edita descripción u orden de un objetivo del docente autenticado.
    def patch(self, request, curso_id, objetivo_id):
        try:
            objetivo = self._obtener(request, curso_id, objetivo_id)
        except ObjetivoCurso.DoesNotExist:
            return Response({'detalle': 'Objetivo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorObjetivo(objetivo, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Elimina un objetivo del docente autenticado.
    def delete(self, request, curso_id, objetivo_id):
        try:
            objetivo = self._obtener(request, curso_id, objetivo_id)
        except ObjetivoCurso.DoesNotExist:
            return Response({'detalle': 'Objetivo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        objetivo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
