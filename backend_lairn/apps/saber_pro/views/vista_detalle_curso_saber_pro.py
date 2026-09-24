"""
Vista de detalle de un curso Saber Pro para el rol Docente (HU-17).

Expone el endpoint `/docente/cursos/<curso_id>/` con cuatro operaciones sobre un
curso específico:
- GET: consulta el detalle, incluido el `codigo` de acceso vigente para compartir
  (HU-17.3).
- PUT / PATCH: edita nombre, descripción o área sin afectar los simulacros ya
  creados en el curso (HU-17.4).
- DELETE: elimina el curso si no conserva historial; si ya tiene simulacros o
  resultados lo desactiva en su lugar, conservando ese historial (HU-17.6).

Todas las operaciones aplican el mismo filtro `docente=request.user`, de modo que
si el curso no existe *o* pertenece a otro docente la respuesta es 404 (no se
revela la existencia de cursos ajenos), igual que `examenes/vista_detalle_curso.py`.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorCursoSaberPro


@extend_schema_view(
    get=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Obtener detalle de curso Saber Pro',
        description='Retorna la información de un curso del docente autenticado, incluido el código de acceso vigente (HU-17.3).',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            200: SerializadorCursoSaberPro,
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    put=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Actualizar curso Saber Pro',
        description='Actualiza la totalidad de los campos editables (nombre, descripción y área) de un curso del docente autenticado.',
        request=SerializadorCursoSaberPro,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            200: SerializadorCursoSaberPro,
            400: OpenApiResponse(description='Datos inválidos o área no indicada'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    patch=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Actualizar curso Saber Pro parcialmente',
        description='Actualiza uno o varios campos editables (nombre, descripción o área) de un curso del docente autenticado.',
        request=SerializadorCursoSaberPro,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            200: SerializadorCursoSaberPro,
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Eliminar o desactivar curso Saber Pro',
        description=(
            'Elimina un curso del docente autenticado si no conserva simulacros ni historial '
            '(revoca el acceso a los estudiantes inscritos). Si el curso ya tiene historial, '
            'solo se desactiva conservando los datos existentes (HU-17.6).'
        ),
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        ],
        responses={
            204: OpenApiResponse(description='Curso eliminado correctamente'),
            200: OpenApiResponse(description='Curso desactivado: conserva su historial'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso no encontrado'),
        },
    ),
)
class VistaDetalleCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    # Recupera el detalle de un curso Saber Pro validando la propiedad del docente.
    def get(self, request, curso_id):
        curso = self._obtener_curso(request, curso_id)
        if isinstance(curso, Response):
            return curso
        return Response(SerializadorCursoSaberPro(curso).data)

    # Actualiza la totalidad de los campos editables del curso (nombre, descripción y área).
    def put(self, request, curso_id):
        return self._actualizar(request, curso_id, parcial=False)

    # Actualiza de forma parcial los campos editables del curso.
    def patch(self, request, curso_id):
        return self._actualizar(request, curso_id, parcial=True)

    # Elimina el curso o lo desactiva según conserve historial (HU-17.6).
    def delete(self, request, curso_id):
        curso = self._obtener_curso(request, curso_id)
        if isinstance(curso, Response):
            return curso

        if curso.tiene_historial():
            curso.activo = False
            curso.save(update_fields=['activo', 'actualizado_en'])
            return Response(
                {
                    'detalle': 'El curso conserva simulacros o resultados y no puede eliminarse: fue desactivado.',
                    'activo': False,
                },
                status=status.HTTP_200_OK,
            )

        curso.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Trae el curso del docente con su área precargada; 404 si no existe o no es suyo.
    def _obtener_curso(self, request, curso_id):
        try:
            return CursoSaberPro.objects.select_related('area').get(
                id=curso_id, docente=request.user
            )
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    # Aplica la actualización parcial o total del curso compartiendo la lógica de guardado.
    def _actualizar(self, request, curso_id, parcial):
        curso = self._obtener_curso(request, curso_id)
        if isinstance(curso, Response):
            return curso

        serializador = SerializadorCursoSaberPro(curso, data=request.data, partial=parcial)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        serializador.save()
        return Response(serializador.data)