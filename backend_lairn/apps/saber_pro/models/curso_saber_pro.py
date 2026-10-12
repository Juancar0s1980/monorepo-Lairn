"""
Modelo de dominio `CursoSaberPro`.

Representa un curso de preparación Saber Pro creado por un docente (HU-17).
A diferencia del curso académico (`examenes.Curso`), NO depende de un plan de
estudios: el docente define el área, el nombre y una descripción, y el sistema
genera y asigna automáticamente un `codigo` alfanumérico único (HU-17.1/17.2)
que el docente comparte con sus estudiantes para que se unan por código (HU-18).

Unicidad y regeneración del código:
- El `codigo` se genera con reintento desde `services/codigos.py` para que el
  docente jamás vea un error de "código duplicado" (HU-17.2).
- Al regenerar (HU-17.3) se reemplaza el valor del campo: como la inscripción
  resuelve el código al momento de unirse, el anterior queda invalidado de
  manera automática.

Desactivación vs eliminación (HU-17.6):
- `activo` permite desactivar un curso conservando simulacros e historial.
- `tiene_historial()` decide en el DELETE si se borra o solo se desactiva.
"""

from django.conf import settings
from django.db import models

from apps.saber_pro.models.area_saber_pro import AreaSaberPro


# Modelo que representa un curso de preparación Saber Pro creado por un docente.
class CursoSaberPro(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    area = models.ForeignKey(
        AreaSaberPro,
        on_delete=models.PROTECT,
        related_name='cursos',
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cursos_saber_pro',
    )
    codigo = models.CharField(
        max_length=8,
        unique=True,
        help_text='Código de acceso autogenerado por el sistema para unirse al curso.',
    )
    activo = models.BooleanField(
        default=True,
        help_text='Permite desactivar el curso conservando su historial (HU-17.6).',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cursos_saber_pro'
        ordering = ['-creado_en']

    def __str__(self):
        return self.nombre

    def tiene_historial(self):
        """Indica si el curso conserva simulacros o resultados que impiden borrarlo.

        HU-17.6: si existe historial, DELETE solo desactiva el curso. El modelo
        `Simulacro` llega en la HU-19; hasta entonces la relación no existe y
        este método devuelve `False` para que el borrado real siempre sea válido.
        """
        relacion_simulacros = getattr(self, 'simulacros', None)
        if relacion_simulacros is None:
            return False
        return relacion_simulacros.exists()