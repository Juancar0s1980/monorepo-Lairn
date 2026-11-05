"""
Serializadores de la revisión docente de consignas abiertas (HU-24).

El docente consulta las respuestas escritas de un intento finalizado y envía
UNA calificación 0.0-5.0 con UNA retroalimentación para el intento completo.
La nota se recalcula en `services.presentaciones.registrar_revision`.
"""

from rest_framework import serializers

from apps.saber_pro.models.respuesta_presentacion import RespuestaPresentacion
from apps.saber_pro.services.presentaciones import (
    presentacion_tiene_revision_pendiente,
)


class SerializadorRevisionPresentacion(serializers.Serializer):
    calificacion = serializers.FloatField(min_value=0, max_value=5)
    retroalimentacion = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class SerializadorRespuestaRevision(serializers.ModelSerializer):
    orden = serializers.IntegerField(source='pregunta.orden', read_only=True)
    tema = serializers.SerializerMethodField()
    contexto = serializers.SerializerMethodField()
    enunciado = serializers.SerializerMethodField()
    texto = serializers.SerializerMethodField()
    palabras = serializers.SerializerMethodField()
    limite_palabras = serializers.SerializerMethodField()

    class Meta:
        model = RespuestaPresentacion
        fields = [
            'id',
            'orden',
            'tema',
            'contexto',
            'enunciado',
            'texto',
            'palabras',
            'limite_palabras',
        ]
        read_only_fields = fields

    def _datos(self, respuesta) -> dict:
        return respuesta.pregunta.datos or {}

    def get_tema(self, respuesta) -> str:
        return self._datos(respuesta).get('tema') or ''

    def get_contexto(self, respuesta) -> str:
        return self._datos(respuesta).get('contexto') or ''

    def get_enunciado(self, respuesta) -> str:
        return self._datos(respuesta).get('enunciado') or ''

    def get_texto(self, respuesta) -> str:
        return str((respuesta.respuesta or {}).get('texto') or '')

    def get_palabras(self, respuesta) -> int:
        return len(self.get_texto(respuesta).split())

    def get_limite_palabras(self, respuesta):
        return self._datos(respuesta).get('limite_palabras')


class SerializadorDetalleRevision(serializers.Serializer):
    presentacion_id = serializers.IntegerField(source='id', read_only=True)
    simulacro_titulo = serializers.CharField(source='simulacro.titulo', read_only=True)
    estudiante_nombre = serializers.SerializerMethodField()
    intento = serializers.IntegerField(read_only=True)
    puntaje = serializers.FloatField(read_only=True)
    calificacion = serializers.SerializerMethodField()
    calificacion_docente = serializers.FloatField(read_only=True, allow_null=True)
    retroalimentacion = serializers.CharField(
        source='retroalimentacion_docente',
        read_only=True,
    )
    revisada_por = serializers.SerializerMethodField()
    revisada_en = serializers.DateTimeField(read_only=True, allow_null=True)
    revision_pendiente = serializers.SerializerMethodField()
    total_consignas = serializers.SerializerMethodField()
    respuestas = serializers.SerializerMethodField()

    def get_estudiante_nombre(self, presentacion) -> str:
        estudiante = presentacion.estudiante
        return f'{estudiante.first_name} {estudiante.first_last_name}'.strip()

    def get_calificacion(self, presentacion) -> float:
        return round(float(presentacion.puntaje or 0) / 20, 2)

    def get_revisada_por(self, presentacion):
        docente = presentacion.revisada_por
        if not docente:
            return None
        return {
            'id': docente.id,
            'nombre_completo': f'{docente.first_name} {docente.first_last_name}'.strip(),
        }

    def get_revision_pendiente(self, presentacion) -> bool:
        return presentacion_tiene_revision_pendiente(presentacion)

    def get_total_consignas(self, presentacion) -> int:
        return sum(
            1
            for pregunta in presentacion.preguntas.all()
            if (pregunta.datos or {}).get('tipo') == 'consigna_escrita'
        )

    def get_respuestas(self, presentacion) -> list:
        respuestas = (
            presentacion.respuestas.select_related('pregunta')
            .filter(es_evaluable=False)
            .order_by('pregunta__orden')
        )
        return SerializadorRespuestaRevision(respuestas, many=True).data