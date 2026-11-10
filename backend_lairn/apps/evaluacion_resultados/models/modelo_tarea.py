"""
Tareas prácticas con rúbrica y sus entregas (HU-08A / HU-08B).

Una tarea es una actividad aparte del momento de evaluación: tiene su propio
plazo (p. ej. domingo 11:59 p. m.), política de entregas tardías, archivos
guía y rúbrica. La crea el docente de la asignatura (a mano o con IA) y la
publica para los estudiantes inscritos en su curso vinculado. Una evaluación
formal de tipo `tarea` (HU-06.4) puede apuntar a una tarea publicada.

Rúbrica (`rubrica`): lista de criterios
  [{"criterio": str, "descripcion": str, "peso": int (suma 100),
    "niveles": [{"nombre": str, "descripcion": str, "valor": float 0-5}]}]
La nota de una entrega = Σ peso/100 × valor del nivel elegido (escala 0-5).

Archivos: guías y entregas van a un almacenamiento PRIVADO (fuera de
MEDIA_ROOT, que se sirve sin autenticación). Solo se descargan por
endpoints que verifican permisos.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

almacenamiento_privado = FileSystemStorage(location=Path(settings.BASE_DIR) / 'archivos_privados')


def _ruta_guia(instancia, nombre):
    return f'tareas/{instancia.tarea_id}/guias/{uuid.uuid4().hex}{Path(nombre).suffix.lower()}'


def _ruta_entrega(instancia, nombre):
    return f'tareas/{instancia.tarea_id}/entregas/{uuid.uuid4().hex}{Path(nombre).suffix.lower()}'


class OpcionesEstadoTarea(models.TextChoices):
    BORRADOR = 'borrador', 'Borrador'
    PUBLICADA = 'publicada', 'Publicada'


class TareaPractica(models.Model):
    asignatura = models.ForeignKey('AsignaturaMalla', on_delete=models.PROTECT, related_name='tareas')
    resultado = models.ForeignKey(
        'ResultadoAprendizaje', on_delete=models.PROTECT, related_name='tareas',
        help_text='RA que evidencia la tarea (trazabilidad DCE).',
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(help_text='Instrucciones completas y entregable esperado.')
    formatos_permitidos = models.JSONField(default=list, help_text='Extensiones aceptadas, p. ej. ["pdf", "zip"].')
    fecha_limite = models.DateTimeField()
    permite_tardias = models.BooleanField(
        default=False, help_text='True: se acepta tarde y se marca "Con retraso". False: se cierra el envío.',
    )
    rubrica = models.JSONField(default=list)
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoTarea.choices, default=OpcionesEstadoTarea.BORRADOR, db_index=True,
    )
    origen = models.CharField(max_length=20, default='manual', help_text='manual | ia')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    publicada_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_tareas'
        ordering = ['-fecha_limite']

    def __str__(self) -> str:
        return f'{self.titulo} ({self.estado})'


class ArchivoGuiaTarea(models.Model):
    tarea = models.ForeignKey('TareaPractica', on_delete=models.CASCADE, related_name='archivos_guia')
    archivo = models.FileField(storage=almacenamiento_privado, upload_to=_ruta_guia)
    nombre_original = models.CharField(max_length=255)
    tamano = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ev_tareas_archivos_guia'
        ordering = ['id']


class EntregaTarea(models.Model):
    tarea = models.ForeignKey('TareaPractica', on_delete=models.PROTECT, related_name='entregas')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    archivo = models.FileField(storage=almacenamiento_privado, upload_to=_ruta_entrega)
    nombre_original = models.CharField(max_length=255)
    tamano = models.PositiveIntegerField()
    enviada_en = models.DateTimeField(auto_now_add=True, help_text='Fecha y hora exactas del envío definitivo.')
    con_retraso = models.BooleanField(default=False)
    # Índice del nivel elegido por criterio, en el orden de la rúbrica.
    niveles_elegidos = models.JSONField(default=list, blank=True)
    nota = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True, default='')
    calificada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    calificada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ev_tareas_entregas'
        ordering = ['enviada_en']
        constraints = [
            # Envío definitivo: una sola entrega por estudiante y tarea (HU-08A.2).
            models.UniqueConstraint(fields=['tarea', 'estudiante'], name='uq_ev_entrega_tarea_estudiante'),
        ]


class OpcionesDecisionPreevaluacion(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de revisión docente'
    APROBADA = 'aprobada', 'Aprobada sin cambios'
    AJUSTADA = 'ajustada', 'Aprobada con ajustes del docente'


class PreevaluacionEntrega(models.Model):
    """Propuesta de la IA para calificar una entrega (HU-15.1 / 15.2 / 15.3).

    Es un borrador SOLO para el docente: el estudiante nunca la ve. La nota
    oficial sigue siendo la de `EntregaTarea`, que solo se escribe cuando el
    docente aprueba (con o sin ajustes) desde "Calificar". Aquí queda la
    trazabilidad: qué propuso la IA, con qué texto y qué decidió el docente.

    `analisis`: [{"criterio": str, "nivel": int, "justificacion": str}] en el orden de la rúbrica.
    """

    entrega = models.OneToOneField('EntregaTarea', on_delete=models.CASCADE, related_name='preevaluacion')
    niveles_propuestos = models.JSONField(default=list)
    nota_propuesta = models.DecimalField(max_digits=3, decimal_places=2)
    analisis = models.JSONField(default=list)
    observaciones_propuestas = models.TextField(blank=True, default='')
    advertencias = models.JSONField(default=list, blank=True, help_text='Límites del análisis (texto recortado, etc.).')
    hash_texto = models.CharField(max_length=64, help_text='SHA-256 del texto analizado.')
    caracteres_analizados = models.PositiveIntegerField(default=0)
    modelo = models.CharField(max_length=100, blank=True, default='')
    generada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    generada_en = models.DateTimeField(auto_now=True)
    decision = models.CharField(
        max_length=20, choices=OpcionesDecisionPreevaluacion.choices,
        default=OpcionesDecisionPreevaluacion.PENDIENTE, db_index=True,
    )
    decidida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ev_tareas_preevaluaciones'
