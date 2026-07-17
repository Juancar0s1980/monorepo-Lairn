"""
Serializers del recurso `Examen`.

Define dos contratos distintos según el consumidor:
- `SerializadorCrearExamen`: usado por el docente para crear, listar y editar
  exámenes. Expone el FK `curso` y todos los parámetros de configuración, e
  incluye validaciones de negocio (rango de `max_intentos` y coherencia entre
  `max_preguntas` y `num_preguntas` en modo maestría) que deben aplicarse en
  cualquier mutación, no solo en el `POST` inicial.
- `SerializadorExamen`: vista para el estudiante; omite el FK `curso` (el
  estudiante ya está en el contexto del curso al consultar) y los campos
  internos de gestión, reduciendo la superficie expuesta.
"""

from rest_framework import serializers
from apps.examenes.models import Examen, ObjetivoCurso
from apps.motor_adaptativo.models import SesionExamen


# Contrato usado por el docente para crear, listar y editar exámenes; incluye validaciones de coherencia.
class SerializadorCrearExamen(serializers.ModelSerializer):
    objetivos = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ObjetivoCurso.objects.all(),
        required=False,
    )

    class Meta:
        model = Examen
        fields = [
            'id', 'curso', 'titulo', 'tema', 'tiempo', 'num_preguntas',
            'retroalimentacion', 'dificultad_inicial', 'max_intentos', 'fecha_limite', 'es_guiado',
            'modo', 'max_preguntas', 'objetivos', 'creado_en'
        ]
        read_only_fields = ['creado_en']

    # Restringe max_intentos al rango [0, 10], donde 0 significa intentos ilimitados.
    def validate_max_intentos(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('max_intentos debe ser entre 0 (ilimitado) y 10.')
        return value

    # Aplica las reglas de negocio que dependen del conjunto completo de campos: coherencia maestría/num_preguntas, objetivos del mismo curso y bloqueo de mutaciones cuando hay sesiones activas.
    def validate(self, data):
        if data.get('modo') == 'maestria':
            num = data.get('num_preguntas', 1)
            max_p = data.get('max_preguntas', 20)
            if max_p < num:
                raise serializers.ValidationError(
                    'max_preguntas debe ser mayor o igual a num_preguntas en modo maestría.'
                )

        # Los objetivos anclados deben pertenecer al mismo curso del examen; si no,
        # el prompt del generador recibiría objetivos de otro temario.
        objetivos = data.get('objetivos')
        if objetivos:
            curso = data.get('curso') or (self.instance.curso if self.instance else None)
            ajenos = [o for o in objetivos if o.curso_id != curso.id]
            if ajenos:
                raise serializers.ValidationError(
                    'Todos los objetivos deben pertenecer al curso del examen.'
                )

        # En operaciones de update (self.instance != None) se bloquea cualquier cambio si hay
        # estudiantes presentando el examen, para no alterar las reglas a mitad de un intento.
        if self.instance is not None and SesionExamen.objects.filter(
            examen=self.instance, estado='en_progreso'
        ).exists():
            raise serializers.ValidationError(
                'No se puede editar el examen porque hay estudiantes presentándolo en este momento.'
            )

        return data


# Vista del examen para el estudiante: omite el FK del curso y los metadatos internos no relevantes.
class SerializadorExamen(serializers.ModelSerializer):
    class Meta:
        model = Examen
        fields = [
            'id', 'titulo', 'tema', 'tiempo', 'num_preguntas',
            'retroalimentacion', 'dificultad_inicial', 'max_intentos', 'fecha_limite', 'es_guiado',
            'modo', 'max_preguntas', 'creado_en'
        ]
