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
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'total_preguntas', 'tema_estudio']
        read_only_fields = ['id', 'creado_en', 'tema_estudio']


class SerializadorLaboratorioDetalleDocente(serializers.ModelSerializer):
    """Detalle para el docente: preguntas completas, incluidos casos de test ocultos."""
    preguntas = SerializadorPreguntaDocente(many=True, read_only=True)

    class Meta:
        model = Laboratorio
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'tema_estudio', 'preguntas']
        read_only_fields = ['id', 'creado_en', 'tema_estudio']


class SerializadorLaboratorioDetalleEstudiante(serializers.ModelSerializer):
    """Detalle para el estudiante: preguntas sin casos de test ocultos."""
    preguntas = SerializadorPreguntaEstudiante(many=True, read_only=True)

    class Meta:
        model = Laboratorio
        fields = ['id', 'titulo', 'instrucciones', 'max_intentos', 'fecha_limite', 'creado_en', 'tema_estudio', 'preguntas']
        read_only_fields = fields
