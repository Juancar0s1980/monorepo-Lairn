"""
Serializers del flujo de inscripción del estudiante por código (HU-18).

- `SerializadorUnirseCursoSaberPro`: contrato de entrada del formulario
  "Unirme a un curso". No es un `ModelSerializer` porque el único dato que el
  estudiante aporta es el `codigo`; la inscripción real se construye en el
  servicio `services/inscripciones.py`. Aquí solo se valida el formato y se
  normaliza a mayúsculas (códigos opacos generados por el sistema, HU-17.2);
  las reglas de dominio (código vigente, curso activo y no duplicado, HU-18.2/
  HU-18.4) viven en el servicio para mantener una sola fuente de verdad y ser
  reutilizables fuera de la vista.
- `SerializadorInscripcionCursoSaberPro`: contrato de salida de una
  inscripción recién creada (HU-18.1/18.3) y del listado de cursos del
  estudiante. Anida el `CursoSaberPro` (con su área) para que el panel lo
  muestre sin consultas adicionales.
"""

from rest_framework import serializers

from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro
from apps.saber_pro.serializers.serializador_curso_saber_pro import SerializadorCursoSaberPro


# Contrato de entrada del formulario de inscripción: solo recibe el código de acceso.
class SerializadorUnirseCursoSaberPro(serializers.Serializer):
    codigo = serializers.CharField(
        max_length=8,
        trim_whitespace=True,
        error_messages={
            'required': 'Ingresa el código de acceso.',
            'blank': 'Ingresa el código de acceso.',
            'max_length': 'El código de acceso tiene 8 caracteres.',
        },
        label='Código de acceso',
        help_text='Código de 8 caracteres que el docente compartió (p. ej. AB3X9KLM).',
    )

    # Normaliza el código a mayúsculas: los códigos los genera el sistema en mayúsculas (HU-17.2).
    def validate_codigo(self, value):
        return value.upper()


# Contrato de salida de una inscripción: la integramos con el curso para el panel.
class SerializadorInscripcionCursoSaberPro(serializers.ModelSerializer):
    curso = SerializadorCursoSaberPro(read_only=True)

    class Meta:
        model = InscripcionCursoSaberPro
        fields = ['id', 'curso', 'fecha']
        read_only_fields = fields
        extra_kwargs = {
            'fecha': {'label': 'Fecha de ingreso al curso'},
        }