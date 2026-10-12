"""
Vista de detalle de un contenido del banco Saber Pro, para el rol Docente (HU-20.3).

Expone `PUT` y `DELETE` sobre `/docente/contenido/<contenido_id>/`:

- PUT: edita el contenido generado (enunciado, opciones, respuesta correcta o
  relaciones de la parte 1 de Inglés, y contexto) antes de aprobarlo. El
  serializer revalida la estructura del área.
- DELETE: descarta el contenido; deja de estar disponible para uso posterior.

Ambas operaciones solo aplican al contenido `pendiente`: una vez aprobado, el
contenido ya forma parte del banco que usan los simulacros (HU-20.4), por lo
que editarlo o borrarlo en silencio rompería esa garantía.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.serializers import SerializadorContenidoBanco, SerializadorEditarContenido


@extend_schema_view(
    put=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Editar contenido pendiente del banco',
        description=(
            'Edita una pregunta o consigna generada por IA antes de aprobarla. '
            'Solo se permite mientras el contenido está pendiente.'
        ),
        request=SerializadorEditarContenido,
        examples=[
            OpenApiExample(
                name='Editar pregunta',
                value={
                    'enunciado': '¿Cuál es el resultado de la operación?',
                    'opciones': ['2', '4', '6', '8'],
                    'respuesta_correcta': '6',
                    'contexto': '',
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Editar parte 1 de Inglés (relacionar)',
                value={
                    'enunciado': 'Match each description with the correct word (A-H).',
                    'opciones': ['sustainable', 'innovation', 'candidate', 'deadline', 'budget', 'venue', 'lecture', 'invoice'],
                    'relaciones': [
                        {'descripcion': 'A long-term approach that does not harm the environment.', 'respuesta': 'sustainable'},
                        {'descripcion': 'A new idea, product or method.', 'respuesta': 'innovation'},
                        {'descripcion': 'A person running for a position or job.', 'respuesta': 'candidate'},
                        {'descripcion': 'The latest date by which something must be finished.', 'respuesta': 'deadline'},
                        {'descripcion': 'A plan of how money will be spent.', 'respuesta': 'budget'},
                    ],
                    'contexto': '',
                },
                request_only=True,
            ),
        ],
        responses={
            200: SerializadorContenidoBanco,
            400: OpenApiResponse(description='Datos inválidos o el contenido ya está aprobado'),
            404: OpenApiResponse(description='Contenido no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Descartar contenido pendiente del banco',
        description='Descarta el contenido generado; no queda disponible para uso posterior.',
        responses={
            204: OpenApiResponse(description='Contenido descartado'),
            400: OpenApiResponse(description='El contenido ya está aprobado'),
            404: OpenApiResponse(description='Contenido no encontrado'),
        },
    ),
)
class VistaDetalleContenidoBancoSaberPro(APIView):
    permission_classes = [EsDocente]

    def _obtener(self, request, contenido_id):
        """Recupera el contenido del docente autenticado o responde 404."""
        try:
            return ContenidoBancoSaberPro.objects.select_related(
                'area', 'competencia', 'afirmacion', 'evidencia',
            ).get(id=contenido_id, docente=request.user), None
        except ContenidoBancoSaberPro.DoesNotExist:
            return None, Response({'detalle': 'Contenido del banco no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, contenido_id):
        contenido, error = self._obtener(request, contenido_id)
        if error:
            return error
        if contenido.estado != 'pendiente':
            return Response(
                {'detalle': 'Solo se puede editar contenido pendiente de aprobación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializador = SerializadorEditarContenido(data=request.data, context={'contenido': contenido})
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        for campo, valor in serializador.validated_data.items():
            setattr(contenido, campo, valor)
        contenido.save()
        return Response(SerializadorContenidoBanco(contenido).data)

    def delete(self, request, contenido_id):
        contenido, error = self._obtener(request, contenido_id)
        if error:
            return error
        if contenido.estado != 'pendiente':
            return Response(
                {'detalle': 'El contenido aprobado ya forma parte del banco; no se puede descartar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contenido.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)