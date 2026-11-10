"""
Serializadores del desbloqueo remoto de simulacros Saber Pro.

El estudiante recibe un resumen mínimo de su solicitud para mostrar la espera en
pantalla. El docente recibe la solicitud con los datos necesarios para
identificar al estudiante, el simulacro y el motivo del bloqueo.
"""

from rest_framework import serializers

from apps.saber_pro.models.solicitud_desbloqueo_simulacro import (
    MOTIVO_SOLICITUD_DESBLOQUEO_CHOICES,
    SolicitudDesbloqueoSimulacro,
)


class SerializadorSolicitudDesbloqueoEstudiante(serializers.ModelSerializer):
    class Meta:
        model = SolicitudDesbloqueoSimulacro
        fields = ['id', 'estado', 'motivo', 'creada_en', 'atendida_en']
        read_only_fields = fields


class SerializadorSolicitudDesbloqueoDocente(serializers.ModelSerializer):
    presentacion_id = serializers.IntegerField(
        source='presentacion.id',
        read_only=True,
    )
    intento = serializers.IntegerField(source='presentacion.intento', read_only=True)
    simulacro_id = serializers.IntegerField(
        source='presentacion.simulacro.id',
        read_only=True,
    )
    simulacro_titulo = serializers.CharField(
        source='presentacion.simulacro.titulo',
        read_only=True,
    )
    curso_id = serializers.IntegerField(
        source='presentacion.simulacro.curso.id',
        read_only=True,
    )
    curso_nombre = serializers.CharField(
        source='presentacion.simulacro.curso.nombre',
        read_only=True,
    )
    area_nombre = serializers.CharField(
        source='presentacion.simulacro.curso.area.nombre',
        read_only=True,
    )
    estudiante = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudDesbloqueoSimulacro
        fields = [
            'id',
            'presentacion_id',
            'intento',
            'simulacro_id',
            'simulacro_titulo',
            'curso_id',
            'curso_nombre',
            'area_nombre',
            'estudiante',
            'motivo',
            'estado',
            'creada_en',
            'atendida_en',
        ]
        read_only_fields = fields

    def get_estudiante(self, solicitud):
        estudiante = solicitud.presentacion.estudiante
        return {
            'id': estudiante.id,
            'nombre_completo': f'{estudiante.first_name} {estudiante.first_last_name}'.strip(),
            'email': estudiante.email,
        }


class SerializadorSolicitarDesbloqueo(serializers.Serializer):
    motivo = serializers.ChoiceField(
        choices=MOTIVO_SOLICITUD_DESBLOQUEO_CHOICES,
        required=False,
        default='cambio_pestana',
    )


class SerializadorListaSolicitudesDesbloqueo(serializers.Serializer):
    total = serializers.IntegerField()
    solicitudes = SerializadorSolicitudDesbloqueoDocente(many=True)
