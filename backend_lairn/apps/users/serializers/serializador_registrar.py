from rest_framework import serializers
from apps.users.models.user import User
from apps.users.models.role import Role


class SerializadorRegistrar(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'first_name',
            'second_name',
            'first_last_name',
            'second_last_name',
            'email',
            'password',
        ]
        extra_kwargs = {
            'first_name': {'label': 'Primer nombre'},
            'second_name': {'label': 'Segundo nombre'},
            'first_last_name': {'label': 'Primer apellido'},
            'second_last_name': {'label': 'Segundo apellido'},
            'email': {'label': 'Correo'},
            'password': {'label': 'Contraseña'},
        }

    def create(self, datos_validados):
        try:
            rol_estudiante = Role.objects.get(name='Estudiante')
        except Role.DoesNotExist:
            raise serializers.ValidationError(
                'Los roles no están inicializados. Ejecuta: python manage.py seed_roles'
            )
        datos_validados['role'] = rol_estudiante
        return User.objects.create_user(**datos_validados)
