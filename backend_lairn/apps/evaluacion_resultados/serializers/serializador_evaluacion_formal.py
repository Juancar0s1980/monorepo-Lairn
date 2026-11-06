"""
Serializadores de la evaluación formal (HU-06).

El momento se asigna en la vista desde la URL (regla de la app: el padre
nunca viene en el payload) y llega aquí por `context['momento']`. El
estado solo cambia con `publicar/`.

Tipo `cuestionario`: preguntas del banco (sin tarea). Tipo `tarea`: exige
una tarea PUBLICADA cuyo RA esté vinculado al momento (HU-06.4).
"""

from rest_framework import serializers

from apps.evaluacion_resultados.models import EvaluacionFormal, OpcionesTipoEvaluacion
from apps.evaluacion_resultados.services.servicio_evaluacion_formal import cobertura, tareas_elegibles

DURACION_MINIMA, DURACION_MAXIMA = 5, 600


class SerializadorEvaluacionFormal(serializers.ModelSerializer):
    total_preguntas = serializers.SerializerMethodField()
    cobertura = serializers.SerializerMethodField()
    momento_nombre = serializers.CharField(source='momento.nombre', read_only=True)
    tarea_titulo = serializers.CharField(source='tarea.titulo', read_only=True, default=None)
    # ADR-009: el supervisor se asigna solo por `evaluaciones/<id>/supervisor/`.
    supervisor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EvaluacionFormal
        fields = [
            'id', 'momento', 'momento_nombre', 'nombre', 'instrucciones', 'tipo', 'tarea', 'tarea_titulo',
            'fecha_inicio', 'fecha_fin', 'duracion_minutos', 'estado',
            'total_preguntas', 'cobertura', 'publicada_en', 'creado_en', 'supervisor', 'supervisor_nombre',
        ]
        read_only_fields = ['momento', 'estado', 'publicada_en', 'creado_en', 'supervisor']

    def get_total_preguntas(self, obj) -> int:
        return obj.items.count()

    def get_supervisor_nombre(self, obj):
        if not obj.supervisor_id:
            return None
        from apps.evaluacion_resultados.services.servicio_supervision import nombre_completo
        return nombre_completo(obj.supervisor)

    def get_cobertura(self, obj) -> list:
        return cobertura(obj)

    def validate_nombre(self, valor: str) -> str:
        valor = (valor or '').strip()
        if not valor:
            raise serializers.ValidationError('El nombre de la evaluación es obligatorio.')
        return valor

    def validate_duracion_minutos(self, valor: int) -> int:
        if not DURACION_MINIMA <= valor <= DURACION_MAXIMA:
            raise serializers.ValidationError(
                f'La duración debe estar entre {DURACION_MINIMA} y {DURACION_MAXIMA} minutos.'
            )
        return valor

    def validate(self, datos):
        inicio = datos.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fin = datos.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        duracion = datos.get('duracion_minutos', getattr(self.instance, 'duracion_minutos', None))
        tipo = datos.get('tipo', getattr(self.instance, 'tipo', OpcionesTipoEvaluacion.CUESTIONARIO))
        tarea = datos.get('tarea', getattr(self.instance, 'tarea', None))
        if tipo == OpcionesTipoEvaluacion.TAREA:
            momento = self.context.get('momento') or getattr(self.instance, 'momento', None)
            if tarea is None:
                raise serializers.ValidationError({'tarea': 'Elige la tarea publicada que se evaluará.'})
            if momento is None or tarea.id not in {t.id for t in tareas_elegibles(momento)}:
                raise serializers.ValidationError(
                    {'tarea': 'La tarea debe estar publicada y evidenciar un RA vinculado a este momento.'}
                )
        else:
            datos['tarea'] = None
        if inicio and fin:
            if fin <= inicio:
                raise serializers.ValidationError({'fecha_fin': 'La fecha de cierre debe ser posterior a la de apertura.'})
            if duracion and duracion * 60 > (fin - inicio).total_seconds():
                raise serializers.ValidationError(
                    {'duracion_minutos': 'La duración no cabe en la ventana de disponibilidad.'}
                )
        return datos


class SerializadorSeleccionPreguntas(serializers.Serializer):
    preguntas = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True, max_length=200)

    def validate_preguntas(self, valor):
        if len(set(valor)) != len(valor):
            raise serializers.ValidationError('Hay preguntas repetidas en la selección.')
        return valor
