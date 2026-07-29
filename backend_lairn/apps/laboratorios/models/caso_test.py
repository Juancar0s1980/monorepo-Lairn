"""
Modelo de dominio `CasoTest`.

Caso de prueba de una `Pregunta` de tipo `codigo` (no aplica a
`respuesta_libre`), definido por el docente. Los casos `es_publico=True` se
muestran al estudiante como ejemplo (igual que los "Example 1/2/3" de un
juez en línea); los `es_publico=False` son ocultos y solo se usan para
calificar, nunca se envían al frontend del estudiante antes de la entrega.
"""

from django.db import models


class CasoTest(models.Model):
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='casos_test'
    )
    entrada = models.TextField(
        blank=True, default='',
        help_text='stdin para Python. No aplica a SQL.'
    )
    salida_esperada = models.TextField(
        help_text='Salida exacta esperada: stdout en Python, resultado serializado en SQL.'
    )
    es_publico = models.BooleanField(
        default=False,
        help_text='Si True, el estudiante lo ve como ejemplo. Si False, es oculto y solo se usa para calificar.'
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'casos_test'
        ordering = ['orden', 'id']
