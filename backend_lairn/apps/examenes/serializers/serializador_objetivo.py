"""
Serializer del recurso `ObjetivoCurso`.

Contrato usado por el docente para crear, listar y editar los objetivos de
aprendizaje de su curso. El FK al curso no se expone como campo de escritura:
la vista lo asigna a partir de la URL (`/cursos/<curso_id>/objetivos/`) tras
validar la propiedad del curso, de modo que un docente no pueda colgar
objetivos en cursos ajenos manipulando el payload.
"""

from rest_framework import serializers
from apps.examenes.models import ObjetivoCurso


class SerializadorObjetivo(serializers.ModelSerializer):
    class Meta:
        model = ObjetivoCurso
        fields = ['id', 'descripcion', 'orden', 'creado_en']
        read_only_fields = ['creado_en']
