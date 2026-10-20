"""
Modelos de trazabilidad operativa: `PerfilAcademico`, `CargueDocumental`
y `RegistroSincronizacion` (HU-03.1 / 03.2).

- `PerfilAcademico`: extiende a `users.User` por OneToOne SIN alterar la
  tabla `users` (no rompe auth/JWT). Guarda documento, matrícula,
  programa y el `external_id` NOVA del usuario.
- `CargueDocumental`: cada PDF subido (pensum / resolución / plan de
  aula) deja rastro: hash del texto, propuesta IA en JSON y quién aprobó.
  El archivo NUNCA se persiste (memoria + descarte, igual que plan de aula).
- `RegistroSincronizacion`: bitácora de cada import/sync (manual, IA o
  API) con contadores y errores, exigible por auditoría TI.
"""

from django.conf import settings
from django.db import models

from .modelo_base import ModeloTrazable


class OpcionesEstadoUsuario(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    EGRESADO = 'egresado', 'Egresado'
    RETIRADO = 'retirado', 'Retirado'


class PerfilAcademico(ModeloTrazable):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_academico',
    )
    numero_documento = models.CharField(max_length=30, blank=True, default='')
    codigo_matricula = models.CharField(
        max_length=30, blank=True, default='', db_index=True,
        help_text='Código o matrícula institucional del estudiante.',
    )
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='perfiles',
    )
    semestre_actual = models.PositiveIntegerField(null=True, blank=True)
    cohorte_ingreso = models.CharField(max_length=20, blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoUsuario.choices,
        default=OpcionesEstadoUsuario.ACTIVO,
    )

    class Meta:
        db_table = 'ev_perfiles_academicos'

    def __str__(self) -> str:
        return f'Perfil {self.usuario_id} ({self.codigo_matricula or "sin matrícula"})'


class OpcionesTipoDocumento(models.TextChoices):
    PENSUM = 'pensum', 'Pensum / Malla curricular'
    RESOLUCION = 'resolucion', 'Resolución / Registro calificado'
    PLAN_AULA = 'plan_aula', 'Plan de aula'


class OpcionesEstadoCargue(models.TextChoices):
    PROCESADO = 'procesado', 'Procesado (propuesta lista)'
    APROBADO = 'aprobado', 'Aprobado e incorporado'
    RECHAZADO = 'rechazado', 'Rechazado'
    FALLIDO = 'fallido', 'Fallido (IA o PDF ilegible)'


class CargueDocumental(models.Model):
    """Rastro auditable de cada documento procesado con IA."""

    tipo = models.CharField(max_length=20, choices=OpcionesTipoDocumento.choices)
    nombre_archivo = models.CharField(
        max_length=255,
        help_text='Solo el nombre, el PDF nunca se guarda en disco.',
    )
    hash_texto = models.CharField(
        max_length=64, db_index=True,
        help_text='SHA256 del texto extraído: evita reprocesar el mismo documento.',
    )
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cargues',
    )
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoCargue.choices,
        default=OpcionesEstadoCargue.PROCESADO,
    )
    propuesta_json = models.JSONField(
        default=dict, blank=True,
        help_text='Propuesta estructurada de la IA pendiente de aprobación humana.',
    )
    detalle_error = models.TextField(blank=True, default='')
    creado_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ev_cargues_documentales'
        ordering = ['-creado_en']

    def __str__(self) -> str:
        return f'{self.get_tipo_display()} {self.nombre_archivo} ({self.estado})'


class RegistroSincronizacion(models.Model):
    """Bitácora de cada sincronización/importación (HU-03)."""

    origen = models.CharField(max_length=20)
    entidad = models.CharField(
        max_length=50,
        help_text='programas / asignaturas / usuarios / matriculas / ...',
    )
    modo = models.CharField(
        max_length=20, default='real',
        help_text='real | simulacro (dry-run: valida sin escribir).',
    )
    total_recibidos = models.PositiveIntegerField(default=0)
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    omitidos = models.PositiveIntegerField(default=0)
    errores = models.JSONField(default=list, blank=True)
    ejecutado_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ev_registros_sincronizacion'
        ordering = ['-creado_en']

    def __str__(self) -> str:
        return f'{self.entidad} {self.origen} +{self.creados} ~{self.actualizados} ({self.modo})'
