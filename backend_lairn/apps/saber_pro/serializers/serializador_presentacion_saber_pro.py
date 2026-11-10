"""
Serializadores de la presentación de simulacros Saber Pro (HU-21).

La regla de seguridad más importante está aquí: `SerializadorPreguntaPresentacion`
expone el bloque actual sin `respuesta_correcta` ni las respuestas de las
relaciones. Las respuestas correctas solo viven en el snapshot interno de la
presentación y en la base de datos.

Los tres contratos públicos son:

- `SerializadorPreguntaPresentacion`: bloque actual sanitizado.
- `SerializadorEstadoPresentacion`: estado del intento, cronómetro, avance y
  resultado cuando ya finalizó.
- `SerializadorResponderPresentacion`: cuerpo del POST de respuesta con sus
  cuatro formas posibles (opción, relaciones, bloque o texto).
"""

from rest_framework import serializers

from apps.saber_pro.serializers.serializador_solicitud_desbloqueo import (
    SerializadorSolicitudDesbloqueoEstudiante,
)
from apps.saber_pro.services.presentaciones import (
    presentacion_tiene_revision_pendiente,
)


class SerializadorPreguntaPresentacion(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    orden = serializers.IntegerField(read_only=True)
    tipo = serializers.SerializerMethodField()
    subtipo = serializers.SerializerMethodField()
    parte = serializers.SerializerMethodField()
    tema = serializers.SerializerMethodField()
    contexto = serializers.SerializerMethodField()
    enunciado = serializers.SerializerMethodField()
    opciones = serializers.SerializerMethodField()
    descripciones = serializers.SerializerMethodField()
    preguntas = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    limite_palabras = serializers.SerializerMethodField()

    def _datos(self, pregunta) -> dict:
        return pregunta.datos or {}

    def get_tipo(self, pregunta) -> str:
        return self._datos(pregunta).get('tipo') or 'seleccion_multiple'

    def get_subtipo(self, pregunta) -> str:
        datos = self._datos(pregunta)
        if datos.get('tipo') == 'consigna_escrita':
            return 'consigna'
        if datos.get('parte') == 1:
            return 'relacionar'
        if datos.get('preguntas'):
            return 'bloque_ingles'
        return 'opcion_multiple'

    def get_parte(self, pregunta):
        return self._datos(pregunta).get('parte')

    def get_tema(self, pregunta) -> str:
        return self._datos(pregunta).get('tema') or ''

    def get_contexto(self, pregunta) -> str:
        return self._datos(pregunta).get('contexto') or ''

    def get_enunciado(self, pregunta) -> str:
        return self._datos(pregunta).get('enunciado') or ''

    def get_opciones(self, pregunta) -> list:
        return list(self._datos(pregunta).get('opciones') or [])

    def get_descripciones(self, pregunta) -> list:
        datos = self._datos(pregunta)
        if datos.get('parte') != 1:
            return []
        return [
            str(relacion.get('descripcion') or '')
            for relacion in datos.get('relaciones') or []
        ]

    def get_preguntas(self, pregunta) -> list:
        datos = self._datos(pregunta)
        return [
            {
                'id': indice,
                'enunciado': str(item.get('enunciado') or ''),
                'opciones': list(item.get('opciones') or []),
            }
            for indice, item in enumerate(datos.get('preguntas') or [], start=1)
        ]

    def get_total_items(self, pregunta) -> int:
        datos = self._datos(pregunta)
        if datos.get('parte') == 1:
            return len(datos.get('relaciones') or [])
        if datos.get('preguntas'):
            return len(datos.get('preguntas') or [])
        return 1

    def get_limite_palabras(self, pregunta):
        return self._datos(pregunta).get('limite_palabras')




class SerializadorResultadoPresentacion(serializers.Serializer):
    anulada = serializers.BooleanField(read_only=True)
    puntaje = serializers.FloatField(read_only=True)
    calificacion = serializers.SerializerMethodField()
    calificacion_docente = serializers.FloatField(read_only=True, allow_null=True)
    retroalimentacion_docente = serializers.CharField(read_only=True)
    correctas = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_evaluables = serializers.IntegerField(read_only=True)
    contenidos_respondidos = serializers.IntegerField(read_only=True)
    total_preguntas = serializers.SerializerMethodField()
    requiere_revision = serializers.BooleanField(read_only=True)
    revision_pendiente = serializers.SerializerMethodField()
    motivo_finalizacion = serializers.CharField(read_only=True)
    finalizada_en = serializers.DateTimeField(read_only=True, allow_null=True)

    def get_total_preguntas(self, presentacion) -> int:
        return presentacion.preguntas.count()

    def get_calificacion(self, presentacion) -> float:
        return round(float(presentacion.puntaje or 0) / 20, 2)

    def get_revision_pendiente(self, presentacion) -> bool:
        return presentacion_tiene_revision_pendiente(presentacion)


class SerializadorEstadoPresentacion(serializers.Serializer):
    presentacion_id = serializers.IntegerField(source='id', read_only=True)
    simulacro_id = serializers.IntegerField(source='simulacro.id', read_only=True)
    simulacro_titulo = serializers.CharField(source='simulacro.titulo', read_only=True)
    curso_nombre = serializers.CharField(source='simulacro.curso.nombre', read_only=True)
    area_nombre = serializers.CharField(source='simulacro.curso.area.nombre', read_only=True)
    intento = serializers.IntegerField(read_only=True)
    estado = serializers.CharField(read_only=True)
    anulada = serializers.BooleanField(read_only=True)
    bloqueada = serializers.BooleanField(read_only=True)
    solicitud_desbloqueo = serializers.SerializerMethodField()
    motivo_finalizacion = serializers.CharField(read_only=True)
    iniciada_en = serializers.DateTimeField(read_only=True)
    expira_en = serializers.DateTimeField(read_only=True)
    finalizada_en = serializers.DateTimeField(read_only=True, allow_null=True)
    fecha_limite = serializers.DateTimeField(source='simulacro.fecha_limite', read_only=True)
    limite_palabras = serializers.IntegerField(source='simulacro.limite_palabras', read_only=True)
    tiempo_limite_minutos = serializers.SerializerMethodField()
    tiempo_restante_segundos = serializers.SerializerMethodField()
    pregunta_numero = serializers.SerializerMethodField()
    total_preguntas = serializers.SerializerMethodField()
    total_items = serializers.IntegerField(read_only=True)
    total_evaluables = serializers.IntegerField(read_only=True)
    contenidos_respondidos = serializers.IntegerField(read_only=True)
    puede_finalizar = serializers.SerializerMethodField()
    finalizada = serializers.SerializerMethodField()
    pregunta = serializers.SerializerMethodField()
    resultado = serializers.SerializerMethodField()

    def get_tiempo_limite_minutos(self, presentacion) -> int:
        return presentacion.simulacro.tiempo_limite_minutos

    def get_tiempo_restante_segundos(self, presentacion) -> int:
        return presentacion.tiempo_restante_segundos()

    def get_solicitud_desbloqueo(self, presentacion):
        solicitud = (
            presentacion.solicitudes_desbloqueo.order_by('-creada_en', '-id').first()
        )
        if solicitud is None:
            return None
        return SerializadorSolicitudDesbloqueoEstudiante(solicitud).data

    def get_total_preguntas(self, presentacion) -> int:
        return presentacion.preguntas.count()

    def get_pregunta_numero(self, presentacion) -> int:
        total = self.get_total_preguntas(presentacion)
        if not presentacion.esta_en_progreso():
            return total
        return min(presentacion.contenidos_respondidos + 1, total)

    def get_puede_finalizar(self, presentacion) -> bool:
        return presentacion.esta_en_progreso()

    def get_finalizada(self, presentacion) -> bool:
        return not presentacion.esta_en_progreso()

    def get_pregunta(self, presentacion):
        if not presentacion.esta_en_progreso():
            return None
        pregunta = self.context.get('pregunta')
        if pregunta is None:
            return None
        return SerializadorPreguntaPresentacion(pregunta).data

    def get_resultado(self, presentacion):
        if presentacion.esta_en_progreso():
            return None
        return SerializadorResultadoPresentacion(presentacion).data


class SerializadorResponderPresentacion(serializers.Serializer):
    pregunta_id = serializers.IntegerField(required=False, min_value=1)
    opcion = serializers.CharField(required=False, allow_blank=True)
    relaciones = serializers.ListField(child=serializers.DictField(), required=False)
    respuestas = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
    texto = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        tipos_enviados = sum(
            attrs.get(campo) is not None
            for campo in ('opcion', 'relaciones', 'respuestas', 'texto')
        )
        if tipos_enviados != 1:
            raise serializers.ValidationError(
                'Envía exactamente un tipo de respuesta: opcion, relaciones, respuestas o texto.'
            )
        return attrs
