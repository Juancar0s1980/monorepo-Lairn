"""
Contrato de entrada del endpoint "generar laboratorio libre": el docente
describe qué laboratorio quiere, en lenguaje natural, y elige el tipo de
ejercicio (código, respuesta abierta, problema con imagen o pronunciación).
`lenguaje` solo es obligatorio (y solo se usa) si `tipo='codigo'` — la IA no
decide el lenguaje en ESE flujo, a diferencia de la sugerencia por objetivo.
"""

from rest_framework import serializers
from apps.laboratorios.models import LENGUAJE_CHOICES, TIPO_CHOICES


class SerializadorSugerirLaboratorioLibre(serializers.Serializer):
    enunciado = serializers.CharField(
        max_length=2000,
        help_text='Descripción libre de qué laboratorio quiere el docente (tema, nivel, tipo de ejercicios).'
    )
    tipo = serializers.ChoiceField(choices=TIPO_CHOICES, default='codigo')
    lenguaje = serializers.ChoiceField(choices=LENGUAJE_CHOICES, required=False)
    cantidad_preguntas = serializers.IntegerField(default=3, min_value=1, max_value=8)

    def validate(self, datos):
        if datos.get('tipo', 'codigo') == 'codigo' and not datos.get('lenguaje'):
            raise serializers.ValidationError({'lenguaje': 'Obligatorio cuando tipo="codigo".'})
        return datos
