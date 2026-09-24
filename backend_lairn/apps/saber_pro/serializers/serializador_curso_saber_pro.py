"""
Serializers del recurso `CursoSaberPro` (HU-17).

Siguen el patrón de `examenes/serializer_curso.py` y de
`users/serializer_gestion_usuario.py` (relación anidada en lectura + `<fk>_id`
en escritura):

- `SerializadorAreaSaberPro`: lectura del área anidada dentro del curso.
- `SerializadorCursoSaberPro`: contrato del docente para crear, listar y editar
  sus cursos. Expone el `area` anidado (lectura) y acepta `area_id` (escritura,
  obligatorio en creación: HU-17.1). `codigo`, `activo` y las fechas son de
  solo lectura porque el código lo genera el sistema (HU-17.2) y la
  desactivación es una decisión del DELETE (HU-17.6).
- `SerializadorCodigoRegenerado`: respuesta del endpoint de regeneración
  (HU-17.3), que devuelve el código nuevo junto al que quedó invalidado.
"""

from rest_framework import serializers

from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro


# Lectura de un área Saber Pro (anidada dentro del curso).
class SerializadorAreaSaberPro(serializers.ModelSerializer):
    class Meta:
        model = AreaSaberPro
        fields = ['id', 'nombre']
        read_only_fields = fields


# Contrato del docente: crear, listar y editar cursos Saber Pro.
class SerializadorCursoSaberPro(serializers.ModelSerializer):
    area = SerializadorAreaSaberPro(read_only=True)
    area_id = serializers.PrimaryKeyRelatedField(
        source='area',
        queryset=AreaSaberPro.objects.all(),
        write_only=True,
        label='Área',
        help_text='ID del área oficial de Saber Pro que se va a preparar (obligatorio).',
    )

    class Meta:
        model = CursoSaberPro
        fields = [
            'id',
            'nombre',
            'descripcion',
            'area',
            'area_id',
            'codigo',
            'activo',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['codigo', 'activo', 'creado_en', 'actualizado_en']
        extra_kwargs = {
            'nombre': {'label': 'Nombre del curso'},
            'descripcion': {'label': 'Descripción'},
        }


# Respuesta del endpoint de regeneración de código (HU-17.3).
class SerializadorCodigoRegenerado(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField(
        help_text='Nuevo código vigente del curso (el anterior quedó invalidado).'
    )
    codigo_anterior = serializers.CharField(help_text='Código que dejó de ser válido.')