"""
Modelo de dominio `Pregunta`.

Pregunta de un laboratorio, curada por el docente (a mano o aceptando una
sugerencia de IA). El campo `tipo` decide qué más aplica:

- `tipo='codigo'`: pregunta de programación tipo juez en línea. El
  `lenguaje` determina qué campos usa:
    - Python/JavaScript/Java/C++/C: `codigo_inicial` es la plantilla que ve
      el estudiante; los `CasoTest` usan `entrada` (stdin) y
      `salida_esperada` (stdout esperado). Java requiere que la clase
      pública se llame `Main`.
    - SQL: `setup_sql` crea y puebla las tablas antes de correr la consulta
      del estudiante (siempre contra una base SQLite en memoria, nunca la
      real); los `CasoTest` de SQL no usan `entrada` como stdin, sino como
      DDL/DML adicional opcional para ese caso puntual.
  Se califica ejecutando en el sandbox y comparando salida exacta (ver
  `services/cliente_ejecutor.py`).

- `tipo='respuesta_libre'`: pregunta de ensayo/respuesta abierta para
  cualquier carrera (Derecho, Inglés, etc.) — el estudiante escribe texto
  libre en vez de código. `lenguaje`/`codigo_inicial`/`setup_sql`/
  `casos_test` no aplican. `criterios_ia` pasa a ser obligatorio: es la
  rúbrica que la IA usa para calificar la respuesta (LLM-as-judge, ver
  `services/agente_evaluador.py`), no una sugerencia opcional.
"""

from django.db import models

TIPO_CHOICES = [
    ('codigo', 'Código'),
    ('respuesta_libre', 'Respuesta abierta'),
]

LENGUAJE_CHOICES = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('java', 'Java'),
    ('cpp', 'C++'),
    ('c', 'C'),
    ('sql', 'SQL'),
]


class Pregunta(models.Model):
    laboratorio = models.ForeignKey(
        'Laboratorio',
        on_delete=models.CASCADE,
        related_name='preguntas'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='codigo')
    enunciado = models.TextField()
    lenguaje = models.CharField(
        max_length=10, choices=LENGUAJE_CHOICES, default='python',
        help_text='Solo aplica si tipo=codigo.'
    )
    codigo_inicial = models.TextField(blank=True, default='')
    setup_sql = models.TextField(
        blank=True, default='',
        help_text='Solo para tipo=codigo y lenguaje=sql: DDL/DML para crear y poblar las tablas antes de la consulta del estudiante.'
    )
    criterios_ia = models.TextField(
        blank=True, default='',
        help_text='Si tipo=respuesta_libre: rúbrica obligatoria que la IA usa para calificar. Si tipo=codigo: instrucciones opcionales para evaluación cualitativa adicional.'
    )
    puntos = models.PositiveIntegerField(default=100)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preguntas_laboratorio'
        ordering = ['orden', 'id']
