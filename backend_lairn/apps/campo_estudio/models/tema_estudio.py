"""
Modelo de dominio `TemaEstudio`.

Un tema de estudio es una explicación acotada a un `Curso`, generada por IA
a partir de su nombre/descripción/objetivos, que el docente debe aprobar
antes de que exista para el estudiante. No hay un estado "rechazado": un
borrador que el docente no quiere se elimina directamente (DELETE), en vez
de acumular un estado que nadie vuelve a consultar.

La eliminación del curso arrastra sus temas por `on_delete=CASCADE`.
"""

from django.db import models

ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('aprobado', 'Aprobado'),
]


class TemaEstudio(models.Model):
    curso = models.ForeignKey(
        'examenes.Curso',
        on_delete=models.CASCADE,
        related_name='temas_estudio'
    )
    titulo = models.CharField(max_length=150)
    contenido = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    aprobado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'temas_estudio'
        ordering = ['-creado_en']
