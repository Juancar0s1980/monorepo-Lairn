from rest_framework import serializers
from apps.users.models.user import User


class SerializadorUsuario(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'second_name',
            'first_last_name',
            'second_last_name',
            'email',
        ]
        extra_kwargs = {
            'first_name': {'label': 'Primer nombre'},
            'second_name': {'label': 'Segundo nombre'},
            'first_last_name': {'label': 'Primer apellido'},
            'second_last_name': {'label': 'Segundo apellido'},
            'email': {'label': 'Correo'},
        }
