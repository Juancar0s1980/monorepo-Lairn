"""
Configuración de la app `evaluacion_resultados`.
"""

from django.apps import AppConfig


class EvaluacionResultadosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.evaluacion_resultados'
    label = 'evaluacion_resultados'
    verbose_name = 'Evaluación de Resultados de Aprendizaje'
