"""
Serializer del listado de estudiantes inscritos a un curso.

Aunque está construido sobre `Inscripcion` (la fuente de verdad de la relación
estudiante-curso), aplana los campos relevantes del estudiante asociado
(`estudiante_id`, `nombre`, `email`) para que el docente consuma una respuesta
plana y centrada en la persona, sin tener que navegar la relación en el cliente.

Vive en un archivo aparte y no junto a los serializers de inscripción porque
representa un caso de uso distinto: la inscripción vista desde la perspectiva
del docente (quién está en su curso) en lugar de desde el estudiante (a qué
curso se unió).
"""

from rest_framework import serializers
from apps.examenes.models import Inscripcion


# Vista aplanada de una inscripción enfocada en los datos del estudiante, usada por el docente.
class SerializadorEstudianteCurso(serializers.ModelSerializer):
    estudiante_id = serializers.IntegerField(source='estudiante.id', read_only=True)
    nombre = serializers.SerializerMethodField()
    email = serializers.EmailField(source='estudiante.email', read_only=True)

    # Concatena nombre y primer apellido del estudiante para exponer un único campo legible.
    def get_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.first_last_name}"

    class Meta:
        model = Inscripcion
        fields = ['id', 'estudiante_id', 'nombre', 'email', 'fecha']
