"""
Serializer del listado de estudiantes inscritos a un curso Saber Pro (HU-17.5).

El recurso de origen es `InscripcionCursoSaberPro`: expone cada inscripción con
los datos de presentación del estudiante (nombre completo y email) y su `fecha`
de ingreso. Mostrar el nombre del estudiante es legítimo porque el endpoint lo
consume el docente propietario del curso, igual que el patrón de
`examenes`/`vista_gestionar_estudiantes.py`.
"""

from rest_framework import serializers

from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro


# Contrato de salida de una inscripción con los datos del estudiante (HU-17.5).
class SerializadorEstudianteInscrito(serializers.ModelSerializer):
    estudiante = serializers.SerializerMethodField()

    class Meta:
        model = InscripcionCursoSaberPro
        fields = ['id', 'estudiante', 'fecha']

    # Devuelve los datos de presentación del estudiante inscrito al curso.
    def get_estudiante(self, obj):
        e = obj.estudiante
        return {
            'id': e.id,
            'nombre_completo': f'{e.first_name} {e.first_last_name}'.strip(),
            'email': e.email,
        }