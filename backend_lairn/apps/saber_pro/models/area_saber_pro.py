"""
Modelo de dominio `AreaSaberPro`.

Representa una de las áreas oficiales de las pruebas Saber Pro que un docente
indica al crear su curso (HU-17.1): Razonamiento Cuantitativo, Lectura Crítica,
Competencias Ciudadanas, Comunicación Escrita e Inglés.

Es un catálogo sembrado (ver `management/commands/seed_saber_pro.py`) en lugar
de un `CharField` con choices para que las épicas siguientes referencien el
mismo registro — HU-19 (distribuciones de simulacros), HU-20 (competencias,
afirmaciones y evidencias) y HU-24 (filtros de analítica) — sin re-migrar el
modelo ni duplicar la lista de áreas.
"""

from django.db import models


# Catálogo de áreas oficiales de las pruebas Saber Pro.
class AreaSaberPro(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, default='')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'areas_saber_pro'
        ordering = ['orden', 'nombre']
        verbose_name = 'Área Saber Pro'
        verbose_name_plural = 'Áreas Saber Pro'

    def __str__(self):
        return self.nombre