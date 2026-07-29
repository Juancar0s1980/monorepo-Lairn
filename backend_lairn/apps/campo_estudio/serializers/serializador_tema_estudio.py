"""
Serializer del recurso `TemaEstudio`.

Sirve tanto para la cola de revisión del docente (incluye `estado`) como para
la lista del estudiante (la vista ya filtra por `estado='aprobado'` antes de
serializar). El FK al curso no se expone como campo de escritura: lo asigna
la vista a partir de la URL, igual que `SerializadorObjetivo`.
"""

from rest_framework import serializers
from apps.campo_estudio.models import TemaEstudio


class SerializadorTemaEstudio(serializers.ModelSerializer):
    class Meta:
        model = TemaEstudio
        fields = ['id', 'titulo', 'contenido', 'estado', 'creado_en', 'aprobado_en']
        read_only_fields = ['id', 'estado', 'creado_en', 'aprobado_en']
