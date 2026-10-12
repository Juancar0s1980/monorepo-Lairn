"""
Modelo de dominio `ContenidoBancoSaberPro` (HU-20).

Unidad del banco de contenido: puede ser una pregunta de selección múltiple
(HU-20.1) o una consigna de escritura para Comunicación Escrita (HU-20.2). El
contenido se genera con IA, queda `pendiente` y solo pasa a `aprobado` cuando
el docente lo revisa y aprueba (HU-20.3); la HU-19 filtrará exclusivamente por
`estado='aprobado'` al ensamblar simulacros (HU-20.4).

Alcance del banco: se ancla a `docente` + `area` (no al curso). Así el banco se
comparte entre los cursos del mismo docente con la misma área, pero cada
docente posee y aprueba su propio contenido: la aprobación de un docente nunca
afecta los simulacros de otro.

Estructura según el área (nunca se mezclan, ver skill de Saber Pro):
- Áreas estructuradas (R. Cuantitativo, Lectura Crítica, Competencias
  Ciudadanas): `tipo='seleccion_multiple'` con 4 opciones y las FK a
  competencia/afirmación/evidencia (la evidencia es opcional: se puede generar
  solo con competencia y afirmación).
- Inglés: `tipo='seleccion_multiple'` con `parte` del 1 al 7, que define la
  tarea y la cantidad de opciones; sin jerarquía competencial. La parte 1 NO es
  de opción múltiple: es de relacionar, ver `relaciones`.
- Comunicación Escrita: `tipo='consigna_escrita'` con `tema`, `contexto` y
  `enunciado`; sin jerarquía competencial ni opciones.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.saber_pro.models.area_saber_pro import AreaSaberPro

TIPO_CONTENIDO_CHOICES = [
    ('seleccion_multiple', 'Selección múltiple'),
    ('consigna_escrita', 'Consigna de escritura'),
]

ESTADO_CONTENIDO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('aprobado', 'Aprobado'),
]


# Contenido generado con IA y almacenado en el banco del docente por área.
class ContenidoBancoSaberPro(models.Model):
    area = models.ForeignKey(
        AreaSaberPro,
        on_delete=models.CASCADE,
        related_name='contenidos_banco',
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contenidos_banco_saber_pro',
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CONTENIDO_CHOICES)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CONTENIDO_CHOICES,
        default='pendiente',
        help_text='Solo el contenido aprobado por el docente alimenta los simulacros (HU-20.4).',
    )

    # Jerarquía académica: presente en las áreas estructuradas, vacía en
    # Comunicación Escrita e Inglés (que evaluán por partes, no por competencias).
    competencia = models.ForeignKey(
        'CompetenciaSaberPro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenidos_banco',
    )
    afirmacion = models.ForeignKey(
        'AfirmacionSaberPro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenidos_banco',
    )
    evidencia = models.ForeignKey(
        'EvidenciaSaberPro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenidos_banco',
    )
    parte = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text='Parte 1 a 7 del examen de Inglés; vacío en las demás áreas.',
    )

    # Cuerpo del contenido. `opciones` y `respuesta_correcta` se usan en las
    # preguntas de selección múltiple; en la parte 1 de Inglés manda
    # `relaciones` (8 palabras para 5 descripciones). `tema`/`contexto` dan
    # soporte tanto a la consigna de escritura como al texto base de Lectura
    # Crítica.
    tema = models.CharField(max_length=200, blank=True, default='')
    contexto = models.TextField(
        blank=True,
        default='',
        help_text='Texto base o situación que enmarca el contenido (máx. 500 palabras en Lectura Crítica).',
    )
    enunciado = models.TextField()
    opciones = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de opciones de respuesta; vacía en consignas de escritura.',
    )
    respuesta_correcta = models.CharField(max_length=500, blank=True, default='')
    relaciones = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'Parte 1 de Inglés: 5 pares {"descripcion", "respuesta"} entre las 5 '
            'descripciones y las 8 palabras (A a H); vacío en los demás contenidos.'
        ),
    )
    preguntas = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'Partes 2 a 7 de Inglés: lista de preguntas del bloque completo, cada una '
            '{"enunciado", "opciones", "respuesta_correcta"}; vacío en los demás contenidos.'
        ),
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    aprobado_en = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Momento en que el docente aprobó el contenido (HU-20.3).',
    )

    class Meta:
        db_table = 'contenidos_banco_saber_pro'
        ordering = ['-creado_en']
        verbose_name = 'Contenido de banco Saber Pro'
        verbose_name_plural = 'Contenidos de banco Saber Pro'
        indexes = [
            # Filtro principal de la HU-19: banco aprobado del área para el docente.
            models.Index(fields=['docente', 'area', 'estado']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(parte__isnull=True) | models.Q(parte__gte=1, parte__lte=7),
                name='contenido_banco_parte_rango',
            ),
        ]

    def __str__(self):
        return f'[{self.get_estado_display()}] {self.enunciado[:60]}'

    def es_pregunta(self):
        """Indica si el contenido tiene forma de pregunta de opción múltiple."""
        return self.tipo == 'seleccion_multiple'
