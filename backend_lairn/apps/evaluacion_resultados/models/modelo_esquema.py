"""
Esquema de calificación del momento (ADR-019).

- Fila con `momento = NULL`: valores **institucionales** (una sola; la edita el Administrador).
- Fila con `momento`: **sobrescritura** de ese momento (la edita el gestor académico).
- Un campo en NULL hereda del nivel superior (momento -> institucional -> constante de
  `escala_institucional`). Los pesos examen/trabajo NO tienen constante: si nadie los define,
  el consolidado de un momento con trabajo queda "Pendiente: ponderación sin definir".
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

_PCT = [MinValueValidator(0), MaxValueValidator(100)]


class EsquemaCalificacion(models.Model):
    momento = models.OneToOneField(
        'MomentoEvaluacion', on_delete=models.CASCADE, null=True, blank=True, related_name='esquema',
    )
    peso_momento_en_corte = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, validators=_PCT,
        help_text='% del tercer corte que vale el momento (Res. 0238/2024: 30).',
    )
    peso_corte_en_definitiva = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, validators=_PCT,
        help_text='% de la nota definitiva que vale el tercer corte (Acuerdo 005, Art. 47: 40).',
    )
    peso_examen = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=_PCT)
    peso_trabajo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=_PCT)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_esquemas_calificacion'
        constraints = [
            models.UniqueConstraint(fields=['momento'], condition=models.Q(momento__isnull=True),
                                    name='uq_ev_esquema_institucional'),
        ]

    def __str__(self) -> str:
        return f'Esquema {self.momento or "institucional"}'
