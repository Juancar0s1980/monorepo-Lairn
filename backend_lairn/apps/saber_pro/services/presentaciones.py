"""
Servicio de presentación de simulacros Saber Pro (HU-21 y HU-22).

Centraliza las reglas que no deben vivir en las vistas:

- iniciar un intento nuevo, cerrando como salida cualquier intento activo;
- congelar el contenido, aleatorizar preguntas y opciones, y fijar el cronómetro;
- entregar únicamente la pregunta actual y sin respuestas correctas;
- registrar respuestas en orden, sin retroceso, y calificarlas;
- finalizar manualmente, al responder el último bloque, al vencer el tiempo, al
  cumplirse la fecha límite del simulacro, cuando el estudiante sale o cuando el
  docente rechaza el desbloqueo de un intento bloqueado;
- guardar la revisión docente de las consignas abiertas.

Durante un intento, cambiar de pestaña, salir de pantalla completa o perder el
foco bloquea la presentación y genera una solicitud de desbloqueo: el intento
no se cierra y el estudiante espera a que su docente lo reanude. Si el docente
rechaza la solicitud, el intento se finaliza y se envía automáticamente.

Un intento nunca se reanuda por navegación. Si el estudiante vuelve a la
pantalla del examen, el intento activo se cierra por salida; cerrar un intento
solo lo finaliza a él y, si aún quedan intentos disponibles, el estudiante puede
iniciar el siguiente.

HU-22.4: durante la presentación no se invoca ningún servicio de IA ni se
entrega retroalimentación; las respuestas correctas solo se usan al calificar.

La calificación se hace por ítem, no por bloque:

- selección múltiple: 1 ítem;
- parte 1 de Inglés: 1 ítem por descripción;
- partes 2 a 7 de Inglés: 1 ítem por subpregunta;
- consigna escrita: se guarda, se limita por palabras y se califica manualmente.

El vencimiento se resuelve de forma perezosa en cada operación. Si no hay un
proceso externo, una presentación vencida queda finalizada en cuanto el
estudiante reanuda, responde, consulta el estado o intenta finalizar.
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.saber_pro.models.presentacion_pregunta import PresentacionPregunta
from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.respuesta_presentacion import RespuestaPresentacion
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.services.aleatorizacion_presentacion import construir_snapshots

MOTIVO_COMPLETADA = 'completada'
MOTIVO_MANUAL = 'manual'
MOTIVO_TIEMPO_AGOTADO = 'tiempo_agotado'
MOTIVO_FECHA_LIMITE = 'fecha_limite'
MOTIVO_SALIDA = 'salida'
MOTIVO_RECHAZADO = 'rechazado'
MOTIVO_ANULADO = 'anulado'


class PresentacionNoDisponibleError(Exception):
    """El simulacro no puede presentarse en este momento."""

    def __init__(self, mensaje='El simulacro no está disponible para presentar.'):
        self.mensaje = mensaje
        super().__init__(mensaje)


class RespuestaInvalidaError(Exception):
    """La respuesta no corresponde al bloque actual o a su estructura."""

    def __init__(self, mensaje):
        self.mensaje = mensaje
        super().__init__(mensaje)


class RevisionInvalidaError(Exception):
    """La calificación docente no corresponde a una respuesta abierta válida."""

    def __init__(self, mensaje):
        self.mensaje = mensaje
        super().__init__(mensaje)


def _normalizar_texto(valor) -> str:
    return str(valor or '').strip().casefold()


def _contar_palabras(texto: str) -> int:
    return len([palabra for palabra in texto.split() if palabra.strip()])


def _total_items(datos: dict) -> int:
    if datos.get('parte') == 1:
        return len(datos.get('relaciones') or [])
    preguntas = datos.get('preguntas') or []
    if preguntas:
        return len(preguntas)
    return 1


def _es_evaluable(datos: dict) -> bool:
    return datos.get('tipo') != 'consigna_escrita'


def _motivo_vencimiento(simulacro, ahora) -> str:
    """Distingue el cierre por plazo del docente del cierre por cronómetro."""
    if simulacro.fecha_limite is not None and ahora >= simulacro.fecha_limite:
        return MOTIVO_FECHA_LIMITE
    return MOTIVO_TIEMPO_AGOTADO


def presentacion_tiene_revision_pendiente(presentacion) -> bool:
    """Indica si el intento tiene consignas abiertas sin calificación docente."""
    return bool(presentacion.requiere_revision) and presentacion.calificacion_docente is None


def _calcular_puntaje(presentacion) -> float:
    """Calcula el puntaje 0-100 del intento.

    Un intento anulado por el docente siempre vale 0, sin importar el avance ni
    las respuestas registradas. Mientras el docente no califique, se conserva el
    puntaje automático sobre los ítems evaluables. Cuando califica, la nota
    0.0-5.0 del docente aporta su fracción a los ítems abiertos del intento (los
    que no se califican solos).
    """
    if presentacion.anulada:
        return 0

    if presentacion.requiere_revision and presentacion.calificacion_docente is not None:
        total = presentacion.total_items
        if not total:
            return 0
        items_abiertos = max(0, total - presentacion.total_evaluables)
        aporte_manual = presentacion.calificacion_docente / 5 * items_abiertos
        return round((presentacion.correctas + aporte_manual) / total * 100, 2)

    if presentacion.total_evaluables:
        return round(presentacion.correctas / presentacion.total_evaluables * 100, 2)
    return 0


@transaction.atomic
def crear_presentacion(simulacro, estudiante) -> PresentacionSimulacro:
    """Inicia un intento nuevo; nunca reanuda el intento activo.

    Se bloquea el simulacro para serializar inicios concurrentes y respetar el
    consecutivo de intentos. Si existe un intento activo, se cierra por salida y
    se devuelve ese mismo intento finalizado para que el estudiante vea su
    resultado sin reanudarlo. Salir solo finaliza ese intento: si al estudiante
    le quedan intentos disponibles, puede iniciar el siguiente.

    Si el intento activo ya venció, se finaliza por tiempo agotado.
    """
    simulacro = Simulacro.objects.select_for_update().select_related('curso').get(
        pk=simulacro.pk
    )

    activa = (
        PresentacionSimulacro.objects.select_for_update()
        .filter(simulacro=simulacro, estudiante=estudiante, estado='en_progreso')
        .order_by('-intento')
        .first()
    )
    if activa is not None:
        if activa.esta_vencida():
            finalizar_presentacion(activa, _motivo_vencimiento(simulacro, timezone.now()))
        else:
            finalizar_presentacion(activa, MOTIVO_SALIDA)
        return activa

    if PresentacionSimulacro.objects.filter(
        simulacro=simulacro,
        estudiante=estudiante,
        anulada=True,
    ).exists():
        raise PresentacionNoDisponibleError(
            'El docente anuló este simulacro para ti; no puedes presentarlo de nuevo.'
        )

    if not simulacro.activo or not simulacro.curso.activo:
        raise PresentacionNoDisponibleError(
            'El simulacro no está disponible para presentar.'
        )

    ahora = timezone.now()
    if simulacro.fecha_limite is not None and ahora >= simulacro.fecha_limite:
        raise PresentacionNoDisponibleError(
            'El plazo para presentar este simulacro ya venció.'
        )

    intentos_realizados = PresentacionSimulacro.objects.filter(
        simulacro=simulacro,
        estudiante=estudiante,
    ).count()
    if intentos_realizados >= simulacro.intentos_maximos:
        raise PresentacionNoDisponibleError(
            f'Ya alcanzaste el máximo de {simulacro.intentos_maximos} '
            f'intento{"s" if simulacro.intentos_maximos != 1 else ""} para este simulacro.'
        )

    asignaciones = list(
        simulacro.preguntas_asignadas.select_related('contenido').order_by('orden', 'id')
    )
    if not asignaciones:
        raise PresentacionNoDisponibleError('El simulacro no tiene preguntas asignadas.')

    intento = (
        simulacro.presentaciones.filter(estudiante=estudiante).aggregate(maximo=Max('intento'))[
            'maximo'
        ]
        or 0
    ) + 1

    pares_aleatorizados = construir_snapshots(simulacro, asignaciones)
    snapshots = [snapshot for _, snapshot in pares_aleatorizados]
    total_items = sum(_total_items(datos) for datos in snapshots)
    total_evaluables = sum(
        _total_items(datos) for datos in snapshots if _es_evaluable(datos)
    )
    requiere_revision = any(not _es_evaluable(datos) for datos in snapshots)
    expira_en = ahora + timedelta(minutes=simulacro.tiempo_limite_minutos)
    if simulacro.fecha_limite is not None:
        expira_en = min(expira_en, simulacro.fecha_limite)

    presentacion = PresentacionSimulacro.objects.create(
        simulacro=simulacro,
        estudiante=estudiante,
        intento=intento,
        iniciada_en=ahora,
        expira_en=expira_en,
        total_items=total_items,
        total_evaluables=total_evaluables,
        requiere_revision=requiere_revision,
    )
    PresentacionPregunta.objects.bulk_create([
        PresentacionPregunta(
            presentacion=presentacion,
            contenido=asignacion.contenido,
            orden=indice,
            datos=snapshot,
        )
        for indice, (asignacion, snapshot) in enumerate(
            pares_aleatorizados,
            start=1,
        )
    ])
    return presentacion


def pregunta_actual(presentacion: PresentacionSimulacro):
    """Bloque que el estudiante debe responder; `None` si ya finalizó."""
    if not presentacion.esta_en_progreso():
        return None
    return (
        presentacion.preguntas.select_related('contenido')
        .filter(orden=presentacion.contenidos_respondidos + 1)
        .first()
    )


def _evaluar_opcion_multiple(datos: dict, respuesta: dict) -> tuple:
    opcion = respuesta.get('opcion')
    if not isinstance(opcion, str) or not opcion.strip():
        raise RespuestaInvalidaError('Selecciona una opción de respuesta.')
    correcta = _normalizar_texto(datos.get('respuesta_correcta')) == _normalizar_texto(opcion)
    return {'opcion': opcion.strip()}, int(correcta), 1, True


def _evaluar_relaciones(datos: dict, respuesta: dict) -> tuple:
    enviadas = respuesta.get('relaciones')
    esperadas = datos.get('relaciones') or []
    if not isinstance(enviadas, list):
        raise RespuestaInvalidaError('Envía las relaciones de la pregunta.')

    indexadas = {}
    for item in enviadas:
        if not isinstance(item, dict):
            raise RespuestaInvalidaError('Cada relación debe incluir descripción y respuesta.')
        descripcion = str(item.get('descripcion') or '').strip()
        valor = str(item.get('respuesta') or '').strip()
        if not descripcion or not valor:
            raise RespuestaInvalidaError('Completa todas las descripciones de la pregunta.')
        clave = _normalizar_texto(descripcion)
        if clave in indexadas:
            raise RespuestaInvalidaError('No repitas una descripción en la respuesta.')
        indexadas[clave] = valor

    claves_esperadas = [_normalizar_texto(item.get('descripcion')) for item in esperadas]
    if set(indexadas) != set(claves_esperadas):
        raise RespuestaInvalidaError('Debes relacionar todas las descripciones de la pregunta.')

    valores_elegidos = [_normalizar_texto(valor) for valor in indexadas.values()]
    if len(set(valores_elegidos)) != len(valores_elegidos):
        raise RespuestaInvalidaError('Cada palabra se puede usar una sola vez.')

    normalizadas = []
    correctas = 0
    for relacion in esperadas:
        descripcion = str(relacion.get('descripcion') or '').strip()
        clave = _normalizar_texto(descripcion)
        valor = indexadas[clave]
        if _normalizar_texto(valor) == _normalizar_texto(relacion.get('respuesta')):
            correctas += 1
        normalizadas.append({'descripcion': descripcion, 'respuesta': valor})

    return {'relaciones': normalizadas}, correctas, len(esperadas), True


def _evaluar_bloque(datos: dict, respuesta: dict) -> tuple:
    enviadas = respuesta.get('respuestas')
    preguntas = datos.get('preguntas') or []
    if not isinstance(enviadas, list):
        raise RespuestaInvalidaError('Envía las respuestas de la pregunta.')
    if len(enviadas) != len(preguntas):
        raise RespuestaInvalidaError('Debes responder todas las preguntas del bloque.')

    normalizadas = []
    correctas = 0
    for indice, (valor, pregunta) in enumerate(zip(enviadas, preguntas), start=1):
        if not isinstance(valor, str) or not valor.strip():
            raise RespuestaInvalidaError(f'Responde la pregunta {indice} del bloque.')
        normalizadas.append(valor.strip())
        if _normalizar_texto(valor) == _normalizar_texto(pregunta.get('respuesta_correcta')):
            correctas += 1

    return {'respuestas': normalizadas}, correctas, len(preguntas), True


def _evaluar_consigna(datos: dict, respuesta: dict) -> tuple:
    texto = respuesta.get('texto')
    if not isinstance(texto, str) or not texto.strip():
        raise RespuestaInvalidaError('Escribe tu respuesta antes de continuar.')
    texto = texto.strip()
    limite = datos.get('limite_palabras')
    if limite and _contar_palabras(texto) > int(limite):
        raise RespuestaInvalidaError(
            f'La consigna admite máximo {limite} palabras. '
            f'Tu respuesta tiene {_contar_palabras(texto)}.'
        )
    return {'texto': texto}, 0, 1, False


def evaluar_respuesta(datos: dict, respuesta: dict) -> tuple:
    """Devuelve `(respuesta_normalizada, correctas, total_items, es_evaluable)`."""
    if datos.get('tipo') == 'consigna_escrita':
        return _evaluar_consigna(datos, respuesta)
    if datos.get('parte') == 1:
        return _evaluar_relaciones(datos, respuesta)
    if datos.get('preguntas'):
        return _evaluar_bloque(datos, respuesta)
    return _evaluar_opcion_multiple(datos, respuesta)


def registrar_respuesta(
    presentacion: PresentacionSimulacro,
    respuesta: dict,
    pregunta_id: int | None = None,
) -> RespuestaPresentacion:
    """Registra la respuesta del bloque actual y avanza o finaliza el intento."""
    if not presentacion.esta_en_progreso():
        raise RespuestaInvalidaError('La presentación ya fue finalizada.')

    if finalizar_si_vencida(presentacion):
        raise RespuestaInvalidaError(
            'El tiempo del intento se agotó y fue finalizado automáticamente.'
        )

    if presentacion.bloqueada:
        raise RespuestaInvalidaError(
            'El intento está bloqueado. Solicita a tu docente que lo desbloquee.'
        )

    actual = pregunta_actual(presentacion)
    if actual is None:
        raise RespuestaInvalidaError('No hay una pregunta pendiente por responder.')
    if pregunta_id is not None and int(pregunta_id) != actual.id:
        raise RespuestaInvalidaError('Solo puedes responder la pregunta actual.')

    normalizada, correctas, total_items, es_evaluable = evaluar_respuesta(
        actual.datos,
        respuesta,
    )
    respuesta_obj = RespuestaPresentacion.objects.create(
        presentacion=presentacion,
        pregunta=actual,
        respuesta=normalizada,
        correctas=correctas,
        total_items=total_items,
        es_evaluable=es_evaluable,
    )

    presentacion.contenidos_respondidos += 1
    if es_evaluable:
        presentacion.correctas += correctas
    else:
        presentacion.requiere_revision = True

    total_preguntas = presentacion.preguntas.count()
    if presentacion.contenidos_respondidos >= total_preguntas:
        finalizar_presentacion(presentacion, MOTIVO_COMPLETADA)
    else:
        presentacion.save(
            update_fields=[
                'contenidos_respondidos',
                'correctas',
                'requiere_revision',
                'actualizado_en',
            ]
        )
    return respuesta_obj


def finalizar_presentacion(
    presentacion: PresentacionSimulacro,
    motivo: str,
) -> PresentacionSimulacro:
    """Finaliza el intento y calcula el puntaje sobre los ítems evaluables."""
    if not presentacion.esta_en_progreso():
        return presentacion

    presentacion.estado = 'finalizada'
    presentacion.motivo_finalizacion = motivo
    presentacion.finalizada_en = timezone.now()
    presentacion.bloqueada = False
    presentacion.puntaje = _calcular_puntaje(presentacion)
    presentacion.save(
        update_fields=[
            'estado',
            'motivo_finalizacion',
            'finalizada_en',
            'bloqueada',
            'contenidos_respondidos',
            'correctas',
            'requiere_revision',
            'puntaje',
            'actualizado_en',
        ]
    )
    presentacion.solicitudes_desbloqueo.filter(estado='pendiente').update(
        estado='cancelada',
        atendida_en=timezone.now(),
    )
    return presentacion


def finalizar_si_vencida(presentacion: PresentacionSimulacro) -> bool:
    """Finaliza por cronómetro o fecha límite si corresponde."""
    if not presentacion.esta_vencida():
        return False
    finalizar_presentacion(
        presentacion,
        _motivo_vencimiento(presentacion.simulacro, timezone.now()),
    )
    return True


def finalizar_por_salida(
    presentacion: PresentacionSimulacro,
) -> PresentacionSimulacro:
    """Cierra el intento por salida del estudiante; es idempotente."""
    if not presentacion.esta_en_progreso():
        return presentacion
    return finalizar_presentacion(presentacion, MOTIVO_SALIDA)


@transaction.atomic
def registrar_revision(presentacion, calificacion, retroalimentacion, docente) -> PresentacionSimulacro:
    """Guarda la calificación del docente para el intento completo.

    El docente asigna una única nota 0.0-5.0 y una retroalimentación a todo el
    intento, no una por consigna. Al terminar se recalcula el puntaje.
    """
    presentacion = PresentacionSimulacro.objects.select_for_update().get(pk=presentacion.pk)

    if presentacion.anulada:
        raise RevisionInvalidaError(
            'El intento fue anulado por el docente y su calificación queda en 0.'
        )
    if presentacion.esta_en_progreso():
        raise RevisionInvalidaError('El intento debe estar finalizado para calificarlo.')
    if not presentacion.requiere_revision:
        raise RevisionInvalidaError('El intento no tiene respuestas abiertas por revisar.')

    presentacion.calificacion_docente = round(float(calificacion), 1)
    presentacion.retroalimentacion_docente = (retroalimentacion or '').strip()
    presentacion.revisada_por = docente
    presentacion.revisada_en = timezone.now()
    presentacion.puntaje = _calcular_puntaje(presentacion)
    presentacion.save(
        update_fields=[
            'calificacion_docente',
            'retroalimentacion_docente',
            'revisada_por',
            'revisada_en',
            'puntaje',
            'actualizado_en',
        ]
    )
    return presentacion