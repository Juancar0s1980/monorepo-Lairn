"""
Modelo de dominio `Simulacro` (HU-19).

Un simulacro pertenece a un curso Saber Pro y hereda de él su área y su
docente. El docente define el título, la descripción, la cantidad de preguntas
(40 por defecto) y el tiempo límite; el sistema ensambla el contenido aprobado
del banco de forma aleatoria (HU-19.3). En Inglés la cantidad no es editable:
siempre se cubren las 7 partes con 45 preguntas fijas.

La distribución académica (competencias, afirmaciones o partes de Inglés) vive
en `DistribucionSimulacro`, y las preguntas concretas asignadas en
`SimulacroPregunta`. Esta separación permite regenerar la selección sin perder
la configuración pedagógica del simulacro.

Disponibilidad (HU-19.5): un simulacro activo de un curso activo está
disponible para los estudiantes inscritos en ese curso; el listado del
estudiante filtra por inscripción y nunca expone respuestas correctas.
"""

from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro


# Simulacro configurado por el docente dentro de un curso Saber Pro.
class Simulacro(models.Model):
    curso = models.ForeignKey(
        'CursoSaberPro',
        on_delete=models.CASCADE,
        related_name='simulacros',
    )
    titulo = models.CharField(max_length=150, blank=True, default='')
    descripcion = models.TextField(blank=True, default='')
    num_preguntas = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        help_text='Cantidad de preguntas que tendrá el simulacro (40 por defecto).',
    )
    tiempo_limite_minutos = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text='Tiempo máximo para presentar el simulacro, en minutos.',
    )
    intentos_maximos = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Cantidad máxima de intentos que puede iniciar cada estudiante.',
    )
    fecha_limite = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora límite para iniciar o continuar el simulacro.',
    )
    limite_palabras = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text='Máximo de palabras por consigna escrita; vacío significa sin límite.',
    )
    activo = models.BooleanField(
        default=True,
        help_text='Un simulacro inactivo deja de estar disponible para los estudiantes.',
    )
    codigo_desbloqueo_hash = models.CharField(
        max_length=128,
        blank=True,
        default='',
        help_text='Hash del codigo que el docente usa para desbloquear un intento.',
    )
    preguntas = models.ManyToManyField(
        ContenidoBancoSaberPro,
        through='SimulacroPregunta',
        related_name='simulacros',
        blank=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'simulacros_saber_pro'
        ordering = ['-creado_en']
        verbose_name = 'Simulacro Saber Pro'
        verbose_name_plural = 'Simulacros Saber Pro'

    def __str__(self):
        return self.titulo or f'Simulacro #{self.id} - {self.curso.nombre}'

    def total_preguntas_asignadas(self):
        """Cantidad de preguntas efectivamente asignadas al simulacro.

        En Inglés cada asignación es un bloque completo de una parte, por lo que
        se suman las preguntas de la parte y no la cantidad de filas. En las
        demás áreas cada asignación aporta una pregunta.
        """
        from apps.saber_pro.services.catalogo_saber_pro import preguntas_de_parte

        total = 0
        for asignacion in self.preguntas_asignadas.all():
            parte = asignacion.contenido.parte
            total += preguntas_de_parte(parte) if parte else 1
        return total

    @property
    def tiene_codigo_desbloqueo(self) -> bool:
        """Indica si el docente configuro un codigo de desbloqueo."""
        return bool(self.codigo_desbloqueo_hash)

    def establecer_codigo_desbloqueo(self, codigo: str) -> None:
        """Guarda el codigo normalizado como hash; nunca conserva texto plano."""
        codigo = (codigo or '').strip().upper()
        self.codigo_desbloqueo_hash = make_password(codigo) if codigo else ''

    def verificar_codigo_desbloqueo(self, codigo: str) -> bool:
        """Compara el codigo recibido con el hash configurado."""
        codigo = (codigo or '').strip().upper()
        return bool(codigo) and self.tiene_codigo_desbloqueo and check_password(
            codigo,
            self.codigo_desbloqueo_hash,
        )

    def tiene_presentaciones_activas(self):
        """Indica si existen presentaciones en curso que impidan editar/eliminar.

        La HU-21 crea `PresentacionSimulacro`; mientras un estudiante tenga un
        intento sin finalizar no se puede modificar la configuración ni
        regenerar las preguntas, porque invalidaría su examen en curso.
        """
        return self.presentaciones.filter(estado='en_progreso').exists()

    def esta_vencido(self) -> bool:
        """Indica si ya pasó la fecha límite configurada por el docente."""
        return self.fecha_limite is not None and timezone.now() >= self.fecha_limite
