"""
Serializer de creación de reportes, para cualquier usuario autenticado.

Exige que el reporte apunte a exactamente uno de `curso` o `examen`: ninguno
de los dos deja el reporte sin contexto sobre qué revisar, y ambos a la vez
mezclaría dos recursos distintos en un solo hilo de moderación.
"""

from rest_framework import serializers
from apps.moderacion.models.reporte import Reporte


class SerializadorCrearReporte(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['id', 'curso', 'examen', 'motivo', 'creado_en']
        read_only_fields = ['creado_en']

    def validate(self, data):
        curso = data.get('curso')
        examen = data.get('examen')
        if not curso and not examen:
            raise serializers.ValidationError('Debes indicar un curso o un examen a reportar.')
        if curso and examen:
            raise serializers.ValidationError('Reporta un curso o un examen, no ambos a la vez.')
        return data
