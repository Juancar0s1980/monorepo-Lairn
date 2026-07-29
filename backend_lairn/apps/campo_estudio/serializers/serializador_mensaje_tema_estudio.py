"""
Serializer del recurso `MensajeTemaEstudio`.

El `estudiante` dueño del hilo no se expone como campo de escritura: la
vista lo asigna a partir de `request.user`, y el `rol` tampoco lo elige el
cliente ('estudiante' o 'ia' se fija según quién genera cada mensaje).
"""

from rest_framework import serializers
from apps.campo_estudio.models import MensajeTemaEstudio


class SerializadorMensajeTemaEstudio(serializers.ModelSerializer):
    class Meta:
        model = MensajeTemaEstudio
        fields = ['id', 'rol', 'contenido', 'creado_en']
        read_only_fields = ['id', 'rol', 'creado_en']
