"""
Modelo de dominio `InscripcionCursoSaberPro`.

Representa la relación N:N entre un Estudiante y un `CursoSaberPro`, materializada
como tabla intermedia explícita para llevar la fecha de ingreso y para ser el
recurso que la HU-18 crea cuando el estudiante se une con el código de acceso.

En HU-17 la consulta del listado de estudiantes inscritos (HU-17.5) parte de
este modelo: el docente del curso ve cada inscripción con su fecha de ingreso.

`unique_together` garantiza a nivel de base de datos que un estudiante no se
inscriba dos veces al mismo curso (HU-18.4), incluso ante condiciones de carrera.
"""

from django.conf import settings
from django.db import models


# Modelo intermedio que materializa la relación estudiante-curso de Saber Pro.
class InscripcionCursoSaberPro(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscripciones_saber_pro',
    )
    curso = models.ForeignKey(
        'CursoSaberPro',
        on_delete=models.CASCADE,
        related_name='inscripciones',
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inscripciones_curso_saber_pro'
        unique_together = ('estudiante', 'curso')
        ordering = ['fecha']

    def __str__(self):
        return f'{self.estudiante.email} → {self.curso.nombre}'