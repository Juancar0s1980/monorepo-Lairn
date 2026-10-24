"""
Serializers del recurso `Laboratorio`.

Separados por rol y por nivel de detalle, siguiendo el mismo patrón que
`examenes`: listas livianas para colecciones, y variantes con `preguntas`
anidadas (ya filtradas por rol) para el detalle.
"""

from rest_framework import serializers
from apps.laboratorios.models import Laboratorio
from .serializador_pregunta import (
    SerializadorPreguntaDocente,
    SerializadorPreguntaEstudiante,
)


class SerializadorLaboratorio(serializers.ModelSerializer):
    """Colección (docente y estudiante): sin preguntas anidadas, solo el conteo."""
    total_preguntas = serializers.IntegerField(source='preguntas.count', read_only=True)

    class Meta:
        model = Laboratorio
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'total_preguntas', 'tema_estudio', 'examen']
        read_only_fields = ['id', 'creado_en', 'tema_estudio', 'examen']


class SerializadorLaboratorioListaEstudiante(SerializadorLaboratorio):
    """Colección (estudiante): suma el progreso del estudiante autenticado en
    cada laboratorio, para que la tarjeta de la lista no se vea "ciega".

    `preguntas_respondidas` se resuelve con un dict pasado por la vista en
    `context['respondidas_por_lab']` ({laboratorio_id: cantidad}) — UNA sola
    consulta agregada para todos los laboratorios de la lista, no una por
    laboratorio (evita N+1 dentro del propio serializer).
    """
    preguntas_respondidas = serializers.SerializerMethodField()

    class Meta(SerializadorLaboratorio.Meta):
        fields = SerializadorLaboratorio.Meta.fields + ['preguntas_respondidas']

    def get_preguntas_respondidas(self, obj):
        return self.context.get('respondidas_por_lab', {}).get(obj.id, 0)


class SerializadorLaboratorioListaDocente(SerializadorLaboratorio):
    """Colección (docente): suma actividad agregada del grupo en cada
    laboratorio (cuántas entregas en total y el puntaje promedio), resuelta
    igual que en `SerializadorLaboratorioListaEstudiante` — un dict
    precalculado por la vista en `context['stats_por_lab']`, no una consulta
    por laboratorio.
    """
    total_entregas = serializers.SerializerMethodField()
    promedio_puntaje = serializers.SerializerMethodField()

    class Meta(SerializadorLaboratorio.Meta):
        fields = SerializadorLaboratorio.Meta.fields + ['total_entregas', 'promedio_puntaje']

    def get_total_entregas(self, obj):
        return self.context.get('stats_por_lab', {}).get(obj.id, {}).get('total', 0)

    def get_promedio_puntaje(self, obj):
        promedio = self.context.get('stats_por_lab', {}).get(obj.id, {}).get('promedio')
        return round(promedio, 1) if promedio is not None else None


class SerializadorLaboratorioDetalleDocente(serializers.ModelSerializer):
    """Detalle para el docente: preguntas completas, incluidos casos de test ocultos."""
    preguntas = SerializadorPreguntaDocente(many=True, read_only=True)

    class Meta:
        model = Laboratorio
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'tema_estudio', 'examen', 'preguntas']
        read_only_fields = ['id', 'creado_en', 'tema_estudio', 'examen']


class SerializadorLaboratorioDetalleEstudiante(serializers.ModelSerializer):
    """Detalle para el estudiante: preguntas sin casos de test ocultos."""
    preguntas = SerializadorPreguntaEstudiante(many=True, read_only=True)

    class Meta:
        model = Laboratorio
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'tema_estudio', 'examen', 'preguntas']
        read_only_fields = fields
