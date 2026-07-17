"""
Modelo de dominio `ObjetivoCurso`.

Representa un objetivo de aprendizaje definido por el docente dentro de su
curso (a mano o aceptando sugerencias de la IA). Los exámenes pueden anclarse
a un subconjunto de estos objetivos: el agente generador recibe sus textos y
está obligado a evaluar uno de ellos en cada pregunta, usando el texto del
objetivo como nombre canónico del concepto. Eso evita que la IA derive hacia
material fuera del temario y estabiliza las claves del modelo de conocimiento.

La eliminación del curso arrastra sus objetivos por `on_delete=CASCADE`.
"""

from django.db import models


class ObjetivoCurso(models.Model):
    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='objetivos'
    )
    descripcion = models.CharField(max_length=200)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'objetivos_curso'
        ordering = ['orden', 'id']
