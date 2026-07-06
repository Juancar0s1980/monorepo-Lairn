from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class SerializadorIniciarSesion(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, datos):
        usuario = authenticate(email=datos['email'], password=datos['password'])
        if not usuario:
            raise serializers.ValidationError('Correo o contraseña incorrectos.')
        token_refresco = RefreshToken.for_user(usuario)
        rol = usuario.role.name if usuario.role else None
        token_refresco['rol'] = rol
        token_refresco.access_token['rol'] = rol
        return {
            'access': str(token_refresco.access_token),
            'refresh': str(token_refresco),
        }
