"""
Vista del hilo de chat de un estudiante sobre un tema de estudio.

Expone `/campo-estudio/temas/<tema_id>/mensajes/` con:
- GET: historial del hilo PROPIO del estudiante (privado — no ve preguntas de
  otros estudiantes sobre el mismo tema).
- POST: guarda la pregunta del estudiante, pide la respuesta a la IA
  (acotada al tema, ver `agente_estudio.responder_pregunta_tema`) y la
  guarda también, devolviendo ambos mensajes.

Solo aplica sobre temas `estado='aprobado'` de cursos donde el estudiante
está inscrito y con `campo_estudio_habilitado=True` — mismas reglas que
`VistaTemasEstudioEstudiante`.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import serializers as drf_serializers
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.campo_estudio.models import TemaEstudio, MensajeTemaEstudio
from apps.campo_estudio.serializers import SerializadorMensajeTemaEstudio
from apps.campo_estudio.services.agente_estudio import responder_pregunta_tema

MAX_MENSAJES_HISTORIAL = 20


@extend_schema_view(
    get=extend_schema(
        tags=['Campo de Estudio'],
        summary='Historial del hilo de un tema (estudiante)',
        parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: SerializadorMensajeTemaEstudio(many=True), 403: OpenApiResponse(description='Sin acceso'), 404: OpenApiResponse(description='Tema no encontrado')},
    ),
    post=extend_schema(
        tags=['Campo de Estudio'],
        summary='Preguntar sobre un tema (estudiante)',
        request=inline_serializer(name='PreguntarTemaEstudio', fields={'pregunta': drf_serializers.CharField()}),
        parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={
            201: SerializadorMensajeTemaEstudio(many=True),
            400: OpenApiResponse(description='Falta la pregunta'),
            403: OpenApiResponse(description='Sin acceso'),
            404: OpenApiResponse(description='Tema no encontrado'),
            502: OpenApiResponse(description='La IA no pudo responder'),
        },
    ),
)
class VistaMensajesTemaEstudio(APIView):
    permission_classes = [EsEstudiante]

    def _obtener_tema_con_acceso(self, request, tema_id):
        """Devuelve el tema si es visible para el estudiante, o (None, Response) con el motivo."""
        try:
            tema = TemaEstudio.objects.select_related('curso').get(id=tema_id, estado='aprobado')
        except TemaEstudio.DoesNotExist:
            return None, Response({'detalle': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=tema.curso).exists():
            return None, Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        if not tema.curso.campo_estudio_habilitado:
            return None, Response({'detalle': 'El Campo de Estudio no está activado para este curso.'}, status=status.HTTP_403_FORBIDDEN)

        return tema, None

    def get(self, request, tema_id):
        tema, error = self._obtener_tema_con_acceso(request, tema_id)
        if error:
            return error

        mensajes = MensajeTemaEstudio.objects.filter(tema=tema, estudiante=request.user)
        return Response(SerializadorMensajeTemaEstudio(mensajes, many=True).data)

    def post(self, request, tema_id):
        tema, error = self._obtener_tema_con_acceso(request, tema_id)
        if error:
            return error

        pregunta = str(request.data.get('pregunta', '')).strip()
        if not pregunta:
            return Response({'detalle': 'La pregunta no puede estar vacía.'}, status=status.HTTP_400_BAD_REQUEST)

        historial_qs = MensajeTemaEstudio.objects.filter(tema=tema, estudiante=request.user).order_by('-creado_en')[:MAX_MENSAJES_HISTORIAL]
        historial = [{'rol': m.rol, 'contenido': m.contenido} for m in reversed(historial_qs)]

        mensaje_estudiante = MensajeTemaEstudio.objects.create(
            tema=tema, estudiante=request.user, rol='estudiante', contenido=pregunta,
        )

        try:
            respuesta = responder_pregunta_tema(
                nombre_curso=tema.curso.nombre,
                titulo_tema=tema.titulo,
                contenido_tema=tema.contenido,
                historial=historial,
                pregunta=pregunta,
            )
        except ValueError as e:
            return Response({'detalle': f'La IA no pudo responder: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        mensaje_ia = MensajeTemaEstudio.objects.create(
            tema=tema, estudiante=request.user, rol='ia', contenido=respuesta,
        )

        return Response(
            SerializadorMensajeTemaEstudio([mensaje_estudiante, mensaje_ia], many=True).data,
            status=status.HTTP_201_CREATED,
        )
