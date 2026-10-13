"""
Modelo `ProgramaAcademico` (HU-01.1 / 01.2 / 01.3).

Catálogo institucional de programas. El `codigo` es el código oficial
(ej. SNIES o código interno U Autónoma) y es único: impide duplicados
aunque el dato venga de manual, documento IA o API.
"""

from django.db import models

from .modelo_base import ModeloTrazable


class ProgramaAcademico(ModeloTrazable):
    codigo = models.CharField(
        max_length=30, unique=True,
        help_text='Código institucional del programa (único, ej. SNIES).',
    )
    nombre = models.CharField(max_length=200)
    modalidad = models.CharField(
        max_length=30, default='Presencial',
        help_text='Presencial / Virtual / Híbrida / Distancia.',
    )
    sede = models.CharField(max_length=100, default='Principal')
    duracion_semestres = models.PositiveIntegerField(
        default=8,
        help_text='Duración total en semestres según resolución.',
    )
    fecha_vigencia = models.DateField(
        null=True, blank=True,
        help_text='Vigencia del registro calificado.',
    )
    estado = models.CharField(
        max_length=20, default='vigente',
        help_text='vigente / en_renovacion / inactivo.',
    )

    class Meta:
        db_table = 'ev_programas'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo', 'estado']),
        ]

    def __str__(self) -> str:
        return f'{self.codigo} - {self.nombre}'
