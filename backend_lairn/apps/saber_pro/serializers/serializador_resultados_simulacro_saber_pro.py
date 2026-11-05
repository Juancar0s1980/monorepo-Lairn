"""
Serializadores de resultados de un simulacro Saber Pro para el docente.

Por defecto la vista entrega el mejor intento de cada estudiante (el de mayor
puntaje entre los ya calificados). Con `?intentos=todos` entrega todos los
intentos finalizados. `puntaje` conserva la escala interna 0-100 y
`calificacion` la traduce a la escala académica 0.0-5.0.
"""

from rest_framework import serializers

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.services.presentaciones import (
    presentacion_tiene_revision_pendiente,
)


class SerializadorResultadoEstudianteSimulacro(serializers.ModelSerializer):
    estudiante = serializers.SerializerMethodField()
    calificacion = serializers.SerializerMethodField()
    aprobado = serializers.SerializerMethodField()
    total_preguntas = serializers.SerializerMethodField()
    revision_pendiente = serializers.SerializerMethodField()
    intentos_pendientes = serializers.SerializerMethodField()

    class Meta:
        model = PresentacionSimulacro
        fields = [
            'id',
            'estudiante',
            'intento',
            'calificacion',
            'aprobado',
            'puntaje',
            'correctas',
            'total_evaluables',
            'contenidos_respondidos',
            'total_preguntas',
            'requiere_revision',
            'revision_pendiente',
            'intentos_pendientes',
            'motivo_finalizacion',
            'iniciada_en',
            'finalizada_en',
        ]
        read_only_fields = fields

    def get_estudiante(self, presentacion):
        estudiante = presentacion.estudiante
        return {
            'id': estudiante.id,
            'nombre_completo': f'{estudiante.first_name} {estudiante.first_last_name}'.strip(),
            'email': estudiante.email,
        }

    def get_calificacion(self, presentacion) -> float:
        return round(presentacion.puntaje / 20, 2)

    def get_aprobado(self, presentacion) -> bool:
        return self.get_calificacion(presentacion) >= 3.0

    def get_total_preguntas(self, presentacion) -> int:
        return presentacion.preguntas.count()

    def get_revision_pendiente(self, presentacion) -> bool:
        return presentacion_tiene_revision_pendiente(presentacion)

    def get_intentos_pendientes(self, presentacion) -> int:
        """Intentos de este estudiante aún sin calificar (lo asigna la vista)."""
        return getattr(presentacion, 'intentos_pendientes', 0)


class SerializadorResumenResultadosSimulacro(serializers.Serializer):
    total_estudiantes = serializers.IntegerField()
    total_intentos = serializers.IntegerField()
    promedio_calificacion = serializers.FloatField()
    aprobados = serializers.IntegerField()
    requieren_revision = serializers.IntegerField()


class SerializadorResultadosSimulacro(serializers.Serializer):
    simulacro_id = serializers.IntegerField()
    simulacro_titulo = serializers.CharField()
    intentos_maximos = serializers.IntegerField()
    resumen = SerializadorResumenResultadosSimulacro()
    resultados = SerializadorResultadoEstudianteSimulacro(many=True)