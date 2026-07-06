"""
Serializer de reportes para el rol Administrador.

Enriquece el reporte con el nombre de quien lo creó y el nombre del curso o
examen reportado, para que el panel de moderación no tenga que resolver esas
referencias por separado. `curso` y `examen` se marcan de solo lectura porque
una vez creado el reporte no tiene sentido reasignarlo a otro recurso; lo
único editable por el administrador es el `estado`.
"""

from rest_framework import serializers
from apps.moderacion.models.reporte import Reporte


class SerializadorReporteAdmin(serializers.ModelSerializer):
    reportado_por = serializers.SerializerMethodField()
    curso_nombre = serializers.SerializerMethodField()
    examen_titulo = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = [
            'id', 'motivo', 'estado', 'creado_en', 'resuelto_en',
            'reportado_por', 'curso', 'curso_nombre', 'examen', 'examen_titulo',
        ]
        read_only_fields = ['creado_en', 'resuelto_en', 'curso', 'examen']

    # Nombre completo de quien creó el reporte.
    def get_reportado_por(self, obj):
        u = obj.reportado_por
        return f"{u.first_name} {u.first_last_name}".strip()

    # Nombre del curso reportado, si aplica.
    def get_curso_nombre(self, obj):
        return obj.curso.nombre if obj.curso else None

    # Título del examen reportado, si aplica.
    def get_examen_titulo(self, obj):
        return obj.examen.titulo if obj.examen else None
