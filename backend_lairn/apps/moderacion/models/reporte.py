"""
Modelo de dominio `Reporte`.

Permite a cualquier usuario autenticado señalar un `Curso` o un `Examen`
problemático para que el Administrador lo revise. Se exige que el reporte
apunte a exactamente uno de los dos recursos (validado en el serializer de
creación), ya que un reporte mezclado sobre ambos diluiría el contexto que
necesita el administrador para actuar.
"""

from django.conf import settings
from django.db import models


ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('resuelto', 'Resuelto'),
    ('descartado', 'Descartado'),
]


class Reporte(models.Model):
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_creados'
    )
    curso = models.ForeignKey(
        'examenes.Curso',
        on_delete=models.CASCADE,
        related_name='reportes',
        null=True,
        blank=True,
    )
    examen = models.ForeignKey(
        'examenes.Examen',
        on_delete=models.CASCADE,
        related_name='reportes',
        null=True,
        blank=True,
    )
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reportes'
