"""
Serializers del recurso `Curso`.

Define tres representaciones distintas del mismo modelo según el caso de uso:
- `SerializadorCrearCurso`: usado por el docente para crear, listar y editar
  sus cursos. Expone el `codigo` y `creado_en` como solo lectura porque son
  generados automáticamente por el modelo.
- `SerializadorCurso`: variante simple sin restricciones de solo lectura, útil
  para escenarios internos o de administración donde el código sí podría
  manipularse.
- `SerializadorCursoEstudiante`: vista pensada para el estudiante; reemplaza
  el FK `docente` por el nombre completo del docente y omite el `codigo`
  porque el alumno no lo necesita una vez inscrito.
"""

from rest_framework import serializers
from apps.examenes.models import Curso


# Contrato usado por el docente para crear, listar y actualizar sus cursos (codigo y fecha son de solo lectura).
class SerializadorCrearCurso(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'descripcion', 'codigo', 'creado_en']
        read_only_fields = ['codigo', 'creado_en']


# Variante plena del curso, sin restricciones de solo lectura, para usos internos o administrativos.
class SerializadorCurso(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'descripcion', 'codigo', 'creado_en']


# Vista del curso pensada para el estudiante: expone el nombre del docente y omite el código de inscripción.
class SerializadorCursoEstudiante(serializers.ModelSerializer):
    docente = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'descripcion', 'docente', 'creado_en']

    # Devuelve el nombre completo del docente concatenando nombre y apellido para presentarlo al estudiante.
    def get_docente(self, obj):
        d = obj.docente
        return f"{d.first_name} {d.first_last_name}".strip()
