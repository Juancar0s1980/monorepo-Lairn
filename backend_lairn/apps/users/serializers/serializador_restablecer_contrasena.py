from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers

from apps.users.services.recuperacion_contrasena import obtener_usuario_desde_uid


class SerializadorRestablecerContrasena(serializers.Serializer):
    uid = serializers.CharField(label='UID')
    token = serializers.CharField(label='Token')
    password = serializers.CharField(write_only=True, label='Nueva contraseña')

    def validate(self, datos):
        usuario = obtener_usuario_desde_uid(datos['uid'])
        if usuario is None or not default_token_generator.check_token(usuario, datos['token']):
            raise serializers.ValidationError('El enlace de recuperación no es válido o ya venció.')
        validate_password(datos['password'], user=usuario)
        datos['usuario'] = usuario
        return datos

    def save(self):
        usuario = self.validated_data['usuario']
        usuario.set_password(self.validated_data['password'])
        usuario.save(update_fields=['password'])
        return usuario
