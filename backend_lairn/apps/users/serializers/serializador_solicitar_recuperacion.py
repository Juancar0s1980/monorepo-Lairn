from rest_framework import serializers


class SerializadorSolicitarRecuperacion(serializers.Serializer):
    email = serializers.EmailField(label='Correo')
