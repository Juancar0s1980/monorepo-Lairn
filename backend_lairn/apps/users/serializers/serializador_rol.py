from rest_framework import serializers
from apps.users.models.role import Role


class SerializadorRol(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']
