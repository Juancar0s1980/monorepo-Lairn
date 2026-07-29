"""
Serializers del recurso `CasoTest`.

Dos variantes por la misma razón que en `Pregunta`: el docente ve y
edita todo (incluye `es_publico` y sirve tanto para casos de ejemplo como
ocultos); el estudiante solo puede ver los casos públicos, sin el campo
`es_publico` (no aporta nada verlo si ya sabe que es público por estar en
la lista).
"""

from rest_framework import serializers
from apps.laboratorios.models import CasoTest


class SerializadorCasoTest(serializers.ModelSerializer):
    """Vista completa (docente): crea/edita casos de test, incluidos los ocultos."""

    class Meta:
        model = CasoTest
        fields = ['id', 'entrada', 'salida_esperada', 'es_publico', 'orden']
        read_only_fields = ['id']


class SerializadorCasoTestPublico(serializers.ModelSerializer):
    """Vista para el estudiante: solo los casos marcados como ejemplo público."""

    class Meta:
        model = CasoTest
        fields = ['id', 'entrada', 'salida_esperada', 'orden']
        read_only_fields = fields
