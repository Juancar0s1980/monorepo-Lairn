"""
Serializadores de tareas prácticas (HU-08A / HU-08B).

- Docente: en borrador se puede guardar con la rúbrica o los formatos
  incompletos (se valida lo que venga); al publicar se exige todo.
- Estudiante: ve la tarea publicada, su plazo y su propia entrega; la
  calificación solo aparece cuando el docente la registró (HU-08A.4).
"""

from rest_framework import serializers

from apps.evaluacion_resultados.models import EntregaTarea, TareaPractica
from apps.evaluacion_resultados.services.servicio_tareas import (
    ErrorRubrica,
    estado_entrega,
    estado_plazo,
    extensiones_permitidas,
    validar_formatos,
    validar_rubrica,
)


def _archivos(tarea):
    return [{'id': a.id, 'nombre': a.nombre_original, 'tamano': a.tamano} for a in tarea.archivos_guia.all()]


class SerializadorTarea(serializers.ModelSerializer):
    asignatura = serializers.SerializerMethodField()
    resultado_descripcion = serializers.CharField(source='resultado.descripcion', read_only=True)
    archivos_guia = serializers.SerializerMethodField()
    total_entregas = serializers.SerializerMethodField()
    estado_plazo = serializers.SerializerMethodField()

    class Meta:
        model = TareaPractica
        fields = [
            'id', 'asignatura', 'resultado', 'resultado_descripcion', 'titulo', 'descripcion',
            'formatos_permitidos', 'fecha_limite', 'permite_tardias', 'rubrica', 'estado', 'origen',
            'archivos_guia', 'total_entregas', 'estado_plazo', 'publicada_en', 'creado_en',
        ]
        read_only_fields = ['estado', 'origen', 'publicada_en', 'creado_en']

    def get_asignatura(self, obj):
        return {'id': obj.asignatura_id, 'codigo': obj.asignatura.codigo, 'nombre': obj.asignatura.nombre}

    def get_archivos_guia(self, obj):
        return _archivos(obj)

    def get_total_entregas(self, obj) -> int:
        return obj.entregas.count()

    def get_estado_plazo(self, obj) -> str:
        return estado_plazo(obj)

    def validate_titulo(self, valor):
        valor = (valor or '').strip()
        if not valor:
            raise serializers.ValidationError('El título es obligatorio.')
        return valor

    def validate_descripcion(self, valor):
        valor = (valor or '').strip()
        if not valor:
            raise serializers.ValidationError('Describe qué deben hacer y entregar los estudiantes.')
        return valor

    def validate_formatos_permitidos(self, valor):
        if valor in (None, []):
            return []
        try:
            return validar_formatos(valor)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_rubrica(self, valor):
        if valor in (None, []):
            return []
        try:
            return validar_rubrica(valor)
        except ErrorRubrica as exc:
            raise serializers.ValidationError(str(exc))


def _calificacion(entrega):
    if entrega is None or entrega.nota is None:
        return None
    return {
        'nota': str(entrega.nota), 'niveles_elegidos': entrega.niveles_elegidos,
        'observaciones': entrega.observaciones, 'calificada_en': entrega.calificada_en,
    }


def _entrega(entrega):
    if entrega is None:
        return None
    return {
        'id': entrega.id, 'nombre': entrega.nombre_original, 'tamano': entrega.tamano,
        'enviada_en': entrega.enviada_en, 'con_retraso': entrega.con_retraso,
        'estado': estado_entrega(entrega), 'calificacion': _calificacion(entrega),
    }


class SerializadorTareaEstudiante(serializers.ModelSerializer):
    asignatura = serializers.SerializerMethodField()
    resultado_descripcion = serializers.CharField(source='resultado.descripcion', read_only=True)
    extensiones = serializers.SerializerMethodField()
    archivos_guia = serializers.SerializerMethodField()
    estado_plazo = serializers.SerializerMethodField()
    mi_entrega = serializers.SerializerMethodField()

    class Meta:
        model = TareaPractica
        fields = [
            'id', 'asignatura', 'resultado_descripcion', 'titulo', 'descripcion', 'formatos_permitidos',
            'extensiones', 'fecha_limite', 'permite_tardias', 'rubrica', 'archivos_guia', 'estado_plazo', 'mi_entrega',
        ]

    def get_asignatura(self, obj):
        return {'id': obj.asignatura_id, 'codigo': obj.asignatura.codigo, 'nombre': obj.asignatura.nombre}

    def get_extensiones(self, obj):
        return sorted(extensiones_permitidas(obj.formatos_permitidos))

    def get_archivos_guia(self, obj):
        return _archivos(obj)

    def get_estado_plazo(self, obj):
        return estado_plazo(obj)

    def get_mi_entrega(self, obj):
        usuario = self.context['request'].user
        return _entrega(EntregaTarea.objects.filter(tarea=obj, estudiante=usuario).first())


def fila_entrega_docente(estudiante, entrega):
    """Fila del panel de entregas (HU-08B.3): incluye a quien no ha entregado."""
    return {
        'estudiante': {
            'id': estudiante.id, 'email': estudiante.email,
            'nombre': f'{estudiante.first_name} {estudiante.first_last_name}'.strip(),
        },
        'entrega': _entrega(entrega),
        'estado': estado_entrega(entrega),
    }


class SerializadorCalificar(serializers.Serializer):
    niveles_elegidos = serializers.ListField(child=serializers.IntegerField(min_value=0), allow_empty=False)
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=3000, default='')
