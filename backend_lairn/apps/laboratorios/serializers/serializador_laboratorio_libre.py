"""
Contrato de entrada del endpoint "generar laboratorio libre": el docente
describe qué laboratorio quiere, en lenguaje natural, y elige explícitamente
el lenguaje de programación (la IA no lo decide en este flujo, a diferencia
de la sugerencia por objetivo).
"""

from rest_framework import serializers
from apps.laboratorios.models import LENGUAJE_CHOICES


class SerializadorSugerirLaboratorioLibre(serializers.Serializer):
    enunciado = serializers.CharField(
        max_length=2000,
        help_text='Descripción libre de qué laboratorio quiere el docente (tema, nivel, tipo de ejercicios).'
    )
    lenguaje = serializers.ChoiceField(choices=LENGUAJE_CHOICES)
    cantidad_preguntas = serializers.IntegerField(default=3, min_value=1, max_value=8)
