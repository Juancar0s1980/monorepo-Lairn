"""
Serializer de gestión de usuarios para el rol Administrador.

Expone el `role` anidado (id y name) para lectura y acepta `role_id` como
campo de escritura para reasignar el rol de un usuario sin tener que anidar
un objeto completo en el request. `is_active` se expone como escribible para
permitir activar/desactivar cuentas sin borrarlas.
"""

from rest_framework import serializers
from apps.users.models.user import User
from apps.users.models.role import Role
from apps.users.serializers.serializador_rol import SerializadorRol


class SerializadorGestionUsuario(serializers.ModelSerializer):
    role = SerializadorRol(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source='role', queryset=Role.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'second_name',
            'first_last_name',
            'second_last_name',
            'email',
            'is_active',
            'role',
            'role_id',
        ]
        read_only_fields = ['email']
