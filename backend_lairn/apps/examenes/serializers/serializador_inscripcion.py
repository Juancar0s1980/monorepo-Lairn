"""
Serializers del recurso `Inscripcion`.

Define los contratos asociados al flujo de auto-inscripción del estudiante:
- `SerializadorInscribirse`: contrato de entrada del formulario de inscripción.
  No es un `ModelSerializer` porque el único dato que el estudiante aporta es
  el `codigo` del curso; la inscripción real se construye en la vista a partir
  del usuario autenticado y del curso resuelto por código.
- `SerializadorInscripcion`: contrato de salida tras una inscripción exitosa,
  reflejando el recurso `Inscripcion` recién creado.
"""

from rest_framework import serializers
from apps.examenes.models import Curso, Inscripcion


# Contrato de entrada del formulario de inscripción: solo recibe el código del curso a unirse.
class SerializadorInscribirse(serializers.Serializer):
    codigo = serializers.CharField(max_length=8)

    # Normaliza el código a mayúsculas y valida que corresponda a un curso existente.
    def validate_codigo(self, value):
        if not Curso.objects.filter(codigo=value.upper()).exists():
            raise serializers.ValidationError('Código de curso inválido.')
        return value.upper()


# Contrato de salida que representa la inscripción recién creada.
class SerializadorInscripcion(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = ['id', 'curso', 'fecha']
