"""
Modelos de dominio para el tipo de pregunta `problema_visual` (opción
múltiple con diagrama generado por IA).

`VarianteProblemaVisual` es una versión concreta de la pregunta: un diagrama
propio y sus propias 4 opciones de respuesta (`respuesta_correcta` es el
índice 0-3 de la opción correcta en `opciones`). Una `Pregunta` de este tipo
tiene varias variantes generadas juntas (ver
`services/agente_problema_visual.generar_variantes_problema_visual`), para
que cada estudiante reciba una distinta y sea más difícil copiarse.

`AsignacionVariante` fija, la primera vez que un estudiante ve la pregunta,
cuál variante le tocó — y se mantiene igual en visitas/intentos
posteriores (no se le vuelve a sortear una nueva cada vez que entra).
"""

from django.conf import settings
from django.db import models


class VarianteProblemaVisual(models.Model):
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='variantes'
    )
    imagen = models.ImageField(upload_to='problemas_visuales/variantes/')
    opciones = models.JSONField(help_text='Lista de 4 textos de opción, ej. ["...", "...", "...", "..."].')
    respuesta_correcta = models.PositiveSmallIntegerField(help_text='Índice (0-3) de la opción correcta en "opciones".')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'variantes_problema_visual'


class AsignacionVariante(models.Model):
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='variantes_asignadas'
    )
    variante = models.ForeignKey(VarianteProblemaVisual, on_delete=models.CASCADE)
    asignado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asignaciones_variante_problema_visual'
        unique_together = ('pregunta', 'estudiante')

    # Recupera la asignación existente o sortea una variante al azar y la fija.
    # Devuelve None si la pregunta todavía no tiene ninguna variante generada.
    @classmethod
    def obtener_o_asignar(cls, pregunta, estudiante):
        try:
            return cls.objects.select_related('variante').get(pregunta=pregunta, estudiante=estudiante)
        except cls.DoesNotExist:
            variante = pregunta.variantes.order_by('?').first()
            if variante is None:
                return None
            return cls.objects.create(pregunta=pregunta, estudiante=estudiante, variante=variante)
