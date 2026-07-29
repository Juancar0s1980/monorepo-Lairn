"""
Modelo de dominio `MensajeTemaEstudio`.

Hilo de chat de un estudiante con la IA sobre un `TemaEstudio` puntual. Es
privado por estudiante: cada quien tiene su propio hilo dentro del mismo
tema (no es un foro compartido del curso), acotado al contenido de ese tema
para que no se convierta en un asistente de IA de propósito general.

La eliminación del tema o del estudiante arrastra sus mensajes por
`on_delete=CASCADE`.
"""

from django.conf import settings
from django.db import models

ROL_CHOICES = [
    ('estudiante', 'Estudiante'),
    ('ia', 'IA'),
]


class MensajeTemaEstudio(models.Model):
    tema = models.ForeignKey(
        'campo_estudio.TemaEstudio',
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_campo_estudio'
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    contenido = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensajes_tema_estudio'
        ordering = ['creado_en']
        indexes = [
            models.Index(fields=['tema', 'estudiante', 'creado_en']),
        ]
