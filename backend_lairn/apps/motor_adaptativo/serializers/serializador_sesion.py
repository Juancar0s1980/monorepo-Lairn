from rest_framework import serializers
from apps.motor_adaptativo.models import SesionExamen


class SerializadorIniciarExamen(serializers.Serializer):
    examen_id = serializers.IntegerField()


class SerializadorResponder(serializers.Serializer):
    respuesta = serializers.CharField()
    tiempo_segundos = serializers.IntegerField()


class SerializadorSesion(serializers.ModelSerializer):
    class Meta:
        model = SesionExamen
        fields = ['id', 'examen', 'dificultad_actual', 'preguntas_respondidas', 'pregunta_actual', 'estado']
