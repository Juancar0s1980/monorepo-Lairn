"""
Centro de ayuda (ADR-018): guías paso a paso de los procedimientos reales de
la plataforma, con video opcional que sube el Administrador.

- `roles`: roles que ven la guía (nombres de `users.Role`). Vacío = todos.
- `pasos`: lista de {"titulo", "detalle"} en orden.
- `video`: archivo propio de la institución (mp4/webm). Se sirve por un
  endpoint autenticado (no por /media), así solo lo ven usuarios con sesión.
"""

from django.conf import settings
from django.db import models


class OpcionesCategoriaAyuda(models.TextChoices):
    PRIMEROS_PASOS = 'primeros_pasos', 'Primeros pasos'
    ESTRUCTURA = 'estructura', 'Estructura curricular'
    DOCENTES = 'docentes', 'Docentes y asignaturas'
    EVALUACIONES = 'evaluaciones', 'Momentos y evaluaciones'
    ESTUDIANTES = 'estudiantes', 'Estudiantes y convocatoria'
    BANCO_TAREAS = 'banco_tareas', 'Banco de preguntas y tareas'
    ANALITICA = 'analitica', 'Analítica e informes'
    IMPORTACION = 'importacion', 'Importación de datos'


class ArticuloAyuda(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    titulo = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=OpcionesCategoriaAyuda.choices)
    roles = models.JSONField(default=list, blank=True, help_text='Roles que la ven; vacío = todos.')
    resumen = models.CharField(max_length=300)
    pasos = models.JSONField(default=list, blank=True)
    notas = models.TextField(blank=True, default='')
    ruta = models.CharField(max_length=200, blank=True, default='', help_text='Pantalla de la plataforma.')
    video = models.FileField(upload_to='ayuda/videos/', blank=True, null=True)
    video_nombre = models.CharField(max_length=200, blank=True, default='')
    orden = models.PositiveIntegerField(default=100)
    publicado = models.BooleanField(default=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        db_table = 'ev_articulos_ayuda'
        ordering = ['categoria', 'orden', 'titulo']

    def __str__(self) -> str:
        return self.titulo
