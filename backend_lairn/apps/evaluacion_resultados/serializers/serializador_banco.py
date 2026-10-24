"""
Serializadores del banco de preguntas (HU-04 / HU-05).

- Lectura: pregunta con su categorización legible (asignatura, RA,
  competencia del RA y competencia transversal) para el panel de curaduría.
- Edición: solo contenido (contexto, enunciado, opciones, respuesta,
  retroalimentación). La categorización y el estado no se editan aquí:
  el estado cambia solo con aprobar/descartar.
"""

from rest_framework import serializers

from apps.evaluacion_resultados.models import PreguntaBanco

MIN_OPCIONES, MAX_OPCIONES = 2, 6


class SerializadorPreguntaBanco(serializers.ModelSerializer):
    asignatura = serializers.SerializerMethodField()
    resultado = serializers.SerializerMethodField()
    competencia_transversal = serializers.SerializerMethodField()

    class Meta:
        model = PreguntaBanco
        fields = [
            'id', 'asignatura', 'resultado', 'competencia_transversal',
            'contexto', 'enunciado', 'opciones', 'respuesta_correcta', 'retroalimentacion',
            'estado', 'origen', 'motivo_descarte', 'revisado_en', 'creado_en', 'actualizado_en',
        ]

    def get_asignatura(self, obj):
        a = obj.asignatura
        return {'id': a.id, 'codigo': a.codigo, 'nombre': a.nombre}

    def get_resultado(self, obj):
        r = obj.resultado
        return {
            'id': r.id, 'descripcion': r.descripcion,
            'competencia': {'id': r.competencia_id, 'nombre': r.competencia.nombre, 'tipo': r.competencia.tipo},
        }

    def get_competencia_transversal(self, obj):
        c = obj.competencia_transversal
        return {'id': c.id, 'nombre': c.nombre} if c else None


class SerializadorEdicionPregunta(serializers.ModelSerializer):
    class Meta:
        model = PreguntaBanco
        fields = ['contexto', 'enunciado', 'opciones', 'respuesta_correcta', 'retroalimentacion']

    def validate_enunciado(self, valor: str) -> str:
        valor = (valor or '').strip()
        if not valor:
            raise serializers.ValidationError('El enunciado es obligatorio.')
        return valor

    def validate_opciones(self, valor):
        if not isinstance(valor, list) or not MIN_OPCIONES <= len(valor) <= MAX_OPCIONES:
            raise serializers.ValidationError(f'Debe haber entre {MIN_OPCIONES} y {MAX_OPCIONES} opciones.')
        if any(not isinstance(o, str) or not o.strip() for o in valor):
            raise serializers.ValidationError('Ninguna opción puede quedar vacía.')
        limpias = [o.strip()[:500] for o in valor]
        if len(set(o.lower() for o in limpias)) != len(limpias):
            raise serializers.ValidationError('Hay opciones repetidas.')
        return limpias

    def validate(self, datos):
        opciones = datos.get('opciones', getattr(self.instance, 'opciones', []))
        correcta = datos.get('respuesta_correcta', getattr(self.instance, 'respuesta_correcta', None))
        if correcta is None or not 0 <= correcta < len(opciones):
            raise serializers.ValidationError({'respuesta_correcta': 'Marca cuál de las opciones es la correcta.'})
        return datos


class SerializadorGenerarPreguntas(serializers.Serializer):
    asignatura = serializers.IntegerField()
    resultado = serializers.IntegerField()
    competencia_transversal = serializers.IntegerField(required=False, allow_null=True)
    cantidad = serializers.IntegerField(min_value=1, max_value=5, default=3)


class SerializadorDescartar(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=300, default='')
