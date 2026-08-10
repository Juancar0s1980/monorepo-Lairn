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

- `tipo='problema_visual'`: problema de opción múltiple con un diagrama
  generado por IA (útil para física, mecánica de fluidos, circuitos, etc.).
  `enunciado` incluye el texto del problema y las fórmulas de apoyo.
  A diferencia de los otros dos tipos, no hay una única imagen/rúbrica: la
  IA genera VARIAS VARIANTES (`variantes`, ver
  `services/agente_problema_visual.py`), cada una con su propio diagrama y
  sus propias 4 opciones de respuesta — el estudiante resuelve a mano en
  papel y solo selecciona la opción correcta (no sube nada, no hay
  calificación por visión: comparar el índice elegido es instantáneo).
  Cada estudiante recibe una variante fija asignada al azar (ver
  `AsignacionVariante`), para dificultar copiarse entre compañeros.
  `imagen_referencia` es opcional: una imagen que el docente sube como guía
  de contexto (no la procesa ninguna IA, es solo para su propia referencia
  o para mostrarle al estudiante el tipo de ejercicio).
  `lenguaje`/`codigo_inicial`/`setup_sql`/`casos_test`/`criterios_ia` no aplican.

- `tipo='pronunciacion'`: práctica de pronunciación (pensado para inglés,
  pero el texto puede ser de cualquier idioma que soporte Edge TTS).
  `texto_pronunciar` es la palabra/frase a practicar; `audio_referencia` es
  su pronunciación correcta, generada con Edge TTS (gratis, sin API key —
  ver `services/agente_pronunciacion.py`) cada vez que se guarda la
  pregunta. El estudiante escucha el audio y graba su propia voz; la
  calificación transcribe esa grabación con Whisper (Groq) y compara el
  texto contra `texto_pronunciar` — sin evaluación fonética fina de acento,
  solo si dijo la palabra/frase correcta.
  `lenguaje`/`codigo_inicial`/`setup_sql`/`casos_test`/`criterios_ia`/
  `imagen_referencia` no aplican.
"""

from django.db import models

TIPO_CHOICES = [
    ('codigo', 'Código'),
    ('respuesta_libre', 'Respuesta abierta'),
    ('problema_visual', 'Problema con imagen'),
    ('pronunciacion', 'Pronunciación'),
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
        help_text='Si tipo=respuesta_libre: rúbrica obligatoria que la IA usa para calificar. Si tipo=codigo: instrucciones opcionales para evaluación cualitativa adicional. No aplica a tipo=problema_visual (calificación por opción múltiple, no por IA).'
    )
    imagen_referencia = models.ImageField(
        upload_to='problemas_visuales/referencias/', null=True, blank=True,
        help_text='Imagen que el docente sube como guía/ejemplo. Opcional, solo contexto — no la procesa ninguna IA. Solo aplica si tipo=problema_visual.'
    )
    texto_pronunciar = models.CharField(
        max_length=300, blank=True, default='',
        help_text='Palabra o frase a pronunciar. Solo aplica si tipo=pronunciacion.'
    )
    audio_referencia = models.FileField(
        upload_to='pronunciacion/referencias/', null=True, blank=True,
        help_text='Audio de la pronunciación correcta, generado con Edge TTS. Solo aplica si tipo=pronunciacion.'
    )
    puntos = models.PositiveIntegerField(default=100)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preguntas_laboratorio'
        ordering = ['orden', 'id']
