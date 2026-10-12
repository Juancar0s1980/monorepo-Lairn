"""
Modelo de dominio `CompetenciaSaberPro` (HU-20).

Primera nivel del catálogo académico de las áreas estructuradas (Razonamiento
Cuantitativo, Lectura Crítica y Competencias Ciudadanas). El docente la
selecciona al generar contenido con IA (HU-20.1) y la HU-19 la usará para
definir la distribución de un simulacro.

Comunicación Escrita e Inglés NO usan esta jerarquía: la primera se evalúa
como consigna de escritura y la segunda por 7 partes con niveles del MCER
(ver `services/catalogo_saber_pro.py`). El catálogo se siembra con
`seed_saber_pro` para que las épicas siguientes compartan los mismos registros.
"""

from django.db import models

from apps.saber_pro.models.area_saber_pro import AreaSaberPro


# Competencia de un área estructurada de Saber Pro.
class CompetenciaSaberPro(models.Model):
    area = models.ForeignKey(
        AreaSaberPro,
        on_delete=models.CASCADE,
        related_name='competencias',
    )
    nombre = models.CharField(max_length=150)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'competencias_saber_pro'
        ordering = ['orden', 'nombre']
        verbose_name = 'Competencia Saber Pro'
        verbose_name_plural = 'Competencias Saber Pro'

    def __str__(self):
        return f'{self.area.nombre} → {self.nombre}'
