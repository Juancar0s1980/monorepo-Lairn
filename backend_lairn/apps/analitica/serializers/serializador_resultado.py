from rest_framework import serializers
from apps.analitica.models import Resultado, RespuestaEstudiante


class SerializadorRespuesta(serializers.ModelSerializer):
    class Meta:
        model = RespuestaEstudiante
        fields = ['concepto', 'pregunta', 'respuesta_correcta', 'respuesta_incorrecta', 'tiempo_por_pregunta', 'dificultad']


class SerializadorResultado(serializers.ModelSerializer):
    respuestas = SerializadorRespuesta(many=True, read_only=True)

    class Meta:
        model = Resultado
        fields = ['id', 'examen', 'puntaje', 'nota', 'total_preguntas', 'correctas', 'completado_en', 'respuestas']
