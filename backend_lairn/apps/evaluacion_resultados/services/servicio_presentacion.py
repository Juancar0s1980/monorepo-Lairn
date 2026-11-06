"""
Reglas de presentación de la evaluación formal (HU-07).

- Convocatoria: estudiantes inscritos en el curso vinculado a alguna
  asignatura de la evaluación (las de sus preguntas o la de su tarea), más
  los convocados extra por cargue masivo (`ConvocadoEvaluacion`, ADR-009).
- Asistencia (ADR-009): si la evaluación tiene supervisor, iniciar exige
  estar marcado presente o tarde (`puede_iniciar_por_asistencia`).
- Activa: publicada y con la hora actual dentro de [fecha_inicio, fecha_fin].
- Cierre: `cerrar_si_vencido` aplica el envío automático (HU-07.3) con lo
  registrado; `cerrar` calcula aciertos y nota (escala 0-5). Un intento
  SUSPENDIDO por integridad (ADR-010) tiene el tiempo congelado: no se cierra.
"""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    ESTADOS_HABILITAN,
    AsistenciaEvaluacion,
    ConvocadoEvaluacion,
    EvaluacionFormal,
    IntentoEvaluacion,
    OpcionesEstadoEvaluacion,
    OpcionesTipoEvaluacion,
)

# Margen para la latencia de red al guardar la última respuesta.
GRACIA_SEGUNDOS = 5


def evaluaciones_convocadas(estudiante):
    """Evaluaciones publicadas a las que el estudiante está convocado (activas o no)."""
    por_preguntas = EvaluacionFormal.objects.filter(
        tipo=OpcionesTipoEvaluacion.CUESTIONARIO,
        items__pregunta__asignatura__curso_vinculado__inscripciones__estudiante=estudiante,
    )
    por_tarea = EvaluacionFormal.objects.filter(
        tipo=OpcionesTipoEvaluacion.TAREA,
        tarea__asignatura__curso_vinculado__inscripciones__estudiante=estudiante,
    )
    ids = set(por_preguntas.values_list('id', flat=True)) | set(por_tarea.values_list('id', flat=True))
    ids |= set(ConvocadoEvaluacion.objects.filter(estudiante=estudiante).values_list('evaluacion_id', flat=True))
    return EvaluacionFormal.objects.filter(
        id__in=ids, estado=OpcionesEstadoEvaluacion.PUBLICADA,
    ).select_related('momento', 'tarea')


def _ids_por_curso(evaluacion) -> set:
    """Estudiantes inscritos en los cursos vinculados a las asignaturas de la evaluación."""
    from apps.examenes.models import Inscripcion

    if evaluacion.tipo == OpcionesTipoEvaluacion.TAREA:
        if not evaluacion.tarea_id:
            return set()
        filtro = {'curso__asignaturas_oficiales__tareas': evaluacion.tarea_id}
    else:
        filtro = {'curso__asignaturas_oficiales__preguntas_banco__evaluaciones_formales': evaluacion.id}
    return set(
        Inscripcion.objects.filter(estudiante__role__name='Estudiante', **filtro)
        .values_list('estudiante_id', flat=True)
    )


def origenes_convocatoria(evaluacion) -> dict:
    """{estudiante_id: 'curso' | 'cargue'}. Si está por ambos, prevalece 'curso'."""
    origen = {i: 'cargue' for i in evaluacion.convocados_extra.values_list('estudiante_id', flat=True)}
    origen.update({i: 'curso' for i in _ids_por_curso(evaluacion)})
    return origen


def convocados_de(evaluacion):
    """Usuarios Estudiante convocados: inscritos en cursos vinculados ∪ convocados por cargue."""
    from apps.users.models import User

    return User.objects.filter(
        id__in=origenes_convocatoria(evaluacion).keys(), role__name='Estudiante',
    ).order_by('first_last_name', 'first_name', 'email')


def asistencia_de(evaluacion, estudiante):
    return AsistenciaEvaluacion.objects.filter(evaluacion=evaluacion, estudiante=estudiante).first()


def puede_iniciar_por_asistencia(evaluacion, estudiante) -> bool:
    """Sin supervisor no hay control; con supervisor solo presente o tarde habilitan."""
    if not evaluacion.supervisor_id:
        return True
    asistencia = asistencia_de(evaluacion, estudiante)
    return asistencia is not None and asistencia.estado in ESTADOS_HABILITAN


def esta_activa(evaluacion, ahora=None) -> bool:
    ahora = ahora or timezone.now()
    return (evaluacion.estado == OpcionesEstadoEvaluacion.PUBLICADA
            and evaluacion.fecha_inicio <= ahora <= evaluacion.fecha_fin)


def calcular_vencimiento(evaluacion, inicio):
    return min(inicio + timedelta(minutes=evaluacion.duracion_minutos), evaluacion.fecha_fin)


def preguntas_de(evaluacion):
    return [i.pregunta for i in evaluacion.items.select_related('pregunta').order_by('orden', 'id')]


def cerrar(intento, *, automatico: bool, momento=None) -> IntentoEvaluacion:
    """Califica y marca enviado. Idempotente: un intento enviado no cambia."""
    with transaction.atomic():
        intento = IntentoEvaluacion.objects.select_for_update().get(pk=intento.pk)
        if intento.enviado or intento.suspendido:
            return intento
        preguntas = preguntas_de(intento.evaluacion)
        aciertos = sum(
            1 for p in preguntas if intento.respuestas.get(str(p.id)) == p.respuesta_correcta
        )
        total = len(preguntas)
        intento.aciertos = aciertos
        intento.total = total
        intento.nota = (Decimal(5) * aciertos / total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total else Decimal('0')
        intento.envio_automatico = automatico
        # Un cierre automático se registra a la hora en que venció, no a la hora en que se detectó.
        intento.enviado_en = momento or timezone.now()
        intento.save()
    return intento


def cerrar_si_vencido(intento, ahora=None) -> IntentoEvaluacion:
    ahora = ahora or timezone.now()
    if intento.suspendido:
        return intento
    if not intento.enviado and ahora > intento.vence_en + timedelta(seconds=GRACIA_SEGUNDOS):
        return cerrar(intento, automatico=True, momento=intento.vence_en)
    return intento
