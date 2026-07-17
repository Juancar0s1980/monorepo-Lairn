"""
Modelo de dominio `PreguntaCodigo`.

Pregunta de código dentro de un laboratorio, curada por el docente (a mano o
aceptando una sugerencia de IA — ver `services/agente_codigo.py`). El
lenguaje determina qué campos aplican:
- Python/JavaScript/Java/C++/C: `codigo_inicial` es la plantilla que ve el
  estudiante; los `CasoTest` usan `entrada` (stdin) y `salida_esperada`
  (stdout esperado). Java requiere que la clase pública se llame `Main`.
- SQL: `setup_sql` crea y puebla las tablas antes de correr la consulta del
  estudiante (siempre contra una base SQLite en memoria, nunca la real);
  los `CasoTest` de SQL no usan `entrada` como stdin, sino como DDL/DML
  adicional opcional para ese caso puntual.

`criterios_ia` es opcional: instrucciones para la evaluación por IA en los
casos donde un test exacto no basta (calidad de código, buenas prácticas,
múltiples soluciones SQL válidas). Ver Fase 4 (calificación).
"""

from django.db import models

LENGUAJE_CHOICES = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('java', 'Java'),
    ('cpp', 'C++'),
    ('c', 'C'),
    ('sql', 'SQL'),
]


class PreguntaCodigo(models.Model):
    laboratorio = models.ForeignKey(
        'Laboratorio',
        on_delete=models.CASCADE,
        related_name='preguntas'
    )
    enunciado = models.TextField()
    lenguaje = models.CharField(max_length=10, choices=LENGUAJE_CHOICES, default='python')
    codigo_inicial = models.TextField(blank=True, default='')
    setup_sql = models.TextField(
        blank=True, default='',
        help_text='Solo para lenguaje=sql: DDL/DML para crear y poblar las tablas antes de la consulta del estudiante.'
    )
    criterios_ia = models.TextField(
        blank=True, default='',
        help_text='Instrucciones para evaluación por IA cuando no basta un test exacto (calidad, buenas prácticas).'
    )
    puntos = models.PositiveIntegerField(default=100)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preguntas_codigo'
        ordering = ['orden', 'id']
