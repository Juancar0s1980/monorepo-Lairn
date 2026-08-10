"""
Modelo de dominio `Examen`.

Representa la configuración de una evaluación dentro de un curso. El examen
no almacena las preguntas: el agente de IA las genera en tiempo real cuando
el estudiante presenta el examen, usando los parámetros declarados acá
(`tema`, `num_preguntas`, `dificultad_inicial`, `modo`, etc.).

Los dos `_CHOICES` se definen como constantes a nivel de módulo para que
puedan reutilizarse desde serializers y vistas sin acoplarse a strings
mágicos, y para que Django los exponga en las migraciones y en el admin.
La eliminación del curso arrastra sus exámenes por `on_delete=CASCADE`.
"""

from django.db import models


# Niveles de dificultad inicial con los que el agente genera la primera pregunta del examen.
DIFICULTAD_CHOICES = [
    (1, 'Fácil'),
    (2, 'Medio'),
    (3, 'Difícil'),
]

# Modos de finalización del examen: cantidad fija de preguntas o criterio de maestría adaptativa.
MODO_CHOICES = [
    ('fijo', 'Fijo'),
    ('maestria', 'Maestría'),
]


# Modelo que describe la configuración de un examen dentro de un curso; las preguntas se generan en runtime.
class Examen(models.Model):
    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='examenes'
    )
    titulo = models.CharField(max_length=200)
    tema = models.CharField(max_length=200)
    tiempo = models.IntegerField(help_text='Duración total en minutos')
    num_preguntas = models.IntegerField(help_text='Mínimo de preguntas. En modo fijo es el total exacto')
    retroalimentacion = models.BooleanField(default=False)
    dificultad_inicial = models.IntegerField(choices=DIFICULTAD_CHOICES, default=2)
    max_intentos = models.IntegerField(default=1, help_text='Número de intentos permitidos. 0 = ilimitado')
    fecha_limite = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha límite para INICIAR un intento nuevo. Vacío = sin límite. No afecta un intento ya en progreso.'
    )
    es_guiado = models.BooleanField(default=False, help_text='Si True, el agente genera una explicación antes de cada pregunta')
    modo = models.CharField(max_length=10, choices=MODO_CHOICES, default='fijo', help_text='Fijo: termina en num_preguntas. Maestría: termina cuando el estudiante domina los conceptos')
    max_preguntas = models.IntegerField(default=20, help_text='Solo en modo maestría. Tope máximo para evitar examen infinito')
    objetivos = models.ManyToManyField(
        'ObjetivoCurso',
        blank=True,
        related_name='examenes',
        help_text='Objetivos del curso que este examen evalúa. Si hay, la IA ancla cada pregunta a uno de ellos'
    )
    peso_practica = models.FloatField(
        default=0,
        help_text='Porcentaje (0-100) que aporta la parte práctica (laboratorio vinculado) a la nota final. 0 = examen solo de teoría.'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'examenes'
