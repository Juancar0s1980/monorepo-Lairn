"""
Servicios de analítica de resultados del módulo Saber Pro (HU-24).

Centraliza los cálculos para que las vistas del docente (HU-24.1/24.2) y de la
analítica institucional (HU-24.3) compartan exactamente las mismas reglas:

- Solo se consideran intentos `finalizada` y sin revisión pendiente, igual que
  el ranking de la HU-23. Un intento con consignas abiertas sin calificar no
  contamina los promedios con un puntaje automático parcial.
- Cada intento elegible aporta a los agregados. Los intentos `anulada` cuentan
  como 0 aciertos pero conservan su denominador de ítems, tal como indica la
  regla de negocio del desbloqueo rechazado.
- El desglose por competencia y afirmación se resuelve con
  `PresentacionPregunta.contenido` (FK al banco). El snapshot `datos` no guarda
  la jerarquía académica; la FK PROTECT garantiza que el criterio no desaparece.
- El periodo académico se deriva de `PresentacionSimulacro.finalizada_en` con
  el formato `AAAA-1` (enero-junio) o `AAAA-2` (julio-diciembre), porque el
  módulo Saber Pro no tiene un campo de periodo propio.
- El filtro por competencia/afirmación refina los desgloses; el resumen y los
  resultados individuales se mantienen sobre el curso/área/periodo elegido.
- Inglés no usa competencia/afirmación: se evalúa por las 7 partes del examen,
  así que su desglose (`por_parte`) y su filtro (`parte=1..7`) sustituyen a los
  de competencia/afirmación sin inventar una jerarquía que el área no tiene.

Las áreas estructuradas traen competencia/afirmación; Inglés y Comunicación
Escrita no, de modo que sus listas de competencia/afirmación quedan vacías sin
inventar desgloses que no correspondan (HU-24.2.3).
"""

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.presentacion_pregunta import PresentacionPregunta
from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.respuesta_presentacion import RespuestaPresentacion
from apps.saber_pro.services.catalogo_saber_pro import (
    AREA_PARTES,
    ESTRUCTURA_PARTES,
    PARTES_INGLES,
    obtener_estructura_area,
)
from apps.saber_pro.services.comparaciones import (
    AreaNoCorrespondeError,
    CursoNoEncontradoError,
    SimulacroNoEncontradoError,
    obtener_curso_docente,
    resolver_simulacro,
    validar_area,
)


class ErrorAnaliticaSaberPro(Exception):
    """Base de los errores de dominio de la analítica Saber Pro (HU-24)."""

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ProgramaNoEncontradoError(ErrorAnaliticaSaberPro):
    """El programa académico (carrera) indicado no existe."""


class CompetenciaNoEncontradaError(ErrorAnaliticaSaberPro):
    """La competencia no existe o no pertenece al área consultada."""


class AfirmacionNoEncontradaError(ErrorAnaliticaSaberPro):
    """La afirmación no existe o no pertenece a la competencia/área consultada."""


class ParteNoCorrespondeError(ErrorAnaliticaSaberPro):
    """La parte no es válida o el área consultada no se evalúa por partes."""


def periodo_de(fecha):
    """Devuelve el periodo académico (`AAAA-1` / `AAAA-2`) de una fecha."""
    if fecha is None:
        return ''
    semestre = 1 if fecha.month <= 6 else 2
    return f'{fecha.year}-{semestre}'


def _rango_periodo(periodo):
    """Convierte un periodo `AAAA-N` en el rango [inicio, fin) de sus fechas."""
    partes = (periodo or '').split('-')
    if len(partes) != 2:
        raise ValueError('El periodo debe tener el formato AAAA-1 o AAAA-2.')
    try:
        anio = int(partes[0])
        semestre = int(partes[1])
    except (TypeError, ValueError):
        raise ValueError('El periodo debe tener el formato AAAA-1 o AAAA-2.')
    if anio < 2000 or semestre not in (1, 2):
        raise ValueError('El periodo debe tener el formato AAAA-1 o AAAA-2.')
    mes = 1 if semestre == 1 else 7
    inicio = timezone.make_aware(datetime(anio, mes, 1))
    if semestre == 1:
        fin = timezone.make_aware(datetime(anio, 7, 1))
    else:
        fin = timezone.make_aware(datetime(anio + 1, 1, 1))
    return inicio, fin


def _porcentaje(aciertos, total):
    """Porcentaje redondeado a dos decimales; 0 cuando no hay ítems."""
    return round(aciertos / total * 100, 2) if total else 0.0


def _promedio(valores):
    """Promedio redondeado a dos decimales; 0 cuando la lista está vacía."""
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def _puntaje_efectivo(presentacion):
    """Puntaje que cuenta para la analítica (0 si el intento fue anulado)."""
    return 0.0 if presentacion.anulada else presentacion.puntaje


def _nombre_completo(estudiante):
    return f'{estudiante.first_name} {estudiante.first_last_name}'.strip()


def _area_ref(area):
    return {'id': area.id, 'nombre': area.nombre}


def _referencia(obj):
    return {'id': obj.id, 'nombre': obj.nombre} if obj is not None else None


def _parte_ref(numero):
    """Referencia legible de una parte de Inglés (1 a 7)."""
    if numero is None:
        return None
    parte = next((item for item in PARTES_INGLES if item['numero'] == numero), None)
    return {
        'numero': numero,
        'nombre': f'Parte {numero}' + (f' · {parte["nombre"]}' if parte else ''),
    }


def _es_area_partes(area):
    return area is not None and obtener_estructura_area(area) == ESTRUCTURA_PARTES


def _resolver_parte(parte, area):
    """Valida que la parte exista y que el área se evalúe por partes de Inglés."""
    if parte is None:
        return None
    if parte < 1 or parte > 7:
        raise ParteNoCorrespondeError('La parte debe estar entre 1 y 7.')
    if area is not None and not _es_area_partes(area):
        raise ParteNoCorrespondeError(
            'El filtro por parte solo aplica al área de Inglés.'
        )
    return parte


def _partes_disponibles(area, simulacro=None):
    """Partes de Inglés que cubre el simulacro (o las 7 del área) para el filtro."""
    if not _es_area_partes(area):
        return []
    numeros = {parte['numero'] for parte in PARTES_INGLES}
    if simulacro is not None:
        configuradas = {
            distribucion.parte
            for distribucion in simulacro.distribuciones.all()
            if distribucion.parte
        }
        if configuradas:
            numeros &= configuradas
    return [
        _parte_ref(parte['numero'])
        for parte in PARTES_INGLES
        if parte['numero'] in numeros
    ]


def _curso_ref(curso):
    return {
        'id': curso.id,
        'nombre': curso.nombre,
        'area': _area_ref(curso.area),
    }


def _simulacro_ref(simulacro):
    if simulacro is None:
        return None
    return {'id': simulacro.id, 'titulo': simulacro.titulo}


def _programa_ref(programa):
    if programa is None:
        return None
    return {'id': programa.id, 'nombre': programa.nombre}


def _perfil_academico(estudiante):
    """Perfil académico del estudiante o None si aún no lo tiene."""
    try:
        return estudiante.perfil_academico
    except ObjectDoesNotExist:
        return None


def _programa_de(estudiante):
    perfil = _perfil_academico(estudiante)
    return perfil.programa if perfil is not None else None


def _presentaciones_base():
    """Intentos finalizados y calificados; base común de toda la analítica."""
    return PresentacionSimulacro.objects.filter(
        estado='finalizada',
    ).filter(Q(requiere_revision=False) | Q(calificacion_docente__isnull=False))


def _con_relaciones(queryset):
    return queryset.select_related(
        'estudiante',
        'estudiante__perfil_academico__programa',
        'simulacro',
        'simulacro__curso',
        'simulacro__curso__area',
    )


def _aplicar_periodo(queryset, periodo):
    if not periodo:
        return queryset
    inicio, fin = _rango_periodo(periodo)
    return queryset.filter(finalizada_en__gte=inicio, finalizada_en__lt=fin)


def _periodos_disponibles(queryset):
    fechas = queryset.values_list('finalizada_en', flat=True)
    return sorted(
        {periodo_de(fecha) for fecha in fechas if fecha is not None},
        reverse=True,
    )


def _resolver_competencia(area, competencia_id):
    if competencia_id is None:
        return None
    competencia = (
        CompetenciaSaberPro.objects.filter(id=competencia_id, area=area)
        .select_related('area')
        .first()
    )
    if competencia is None:
        raise CompetenciaNoEncontradaError(
            'La competencia indicada no pertenece al área seleccionada.'
        )
    return competencia


def _resolver_afirmacion(area, afirmacion_id, competencia=None):
    if afirmacion_id is None:
        return None
    afirmacion = (
        AfirmacionSaberPro.objects.filter(
            id=afirmacion_id,
            competencia__area=area,
        )
        .select_related('competencia__area')
        .first()
    )
    if afirmacion is None:
        raise AfirmacionNoEncontradaError(
            'La afirmación indicada no pertenece al área seleccionada.'
        )
    if competencia is not None and afirmacion.competencia_id != competencia.id:
        raise AfirmacionNoEncontradaError(
            'La afirmación indicada no pertenece a la competencia seleccionada.'
        )
    return afirmacion


def _filtrar_presentaciones(queryset):
    return queryset.order_by(
        'simulacro__curso__nombre',
        'simulacro__curso_id',
        'simulacro_id',
        'estudiante__first_last_name',
        'estudiante__first_name',
        'estudiante_id',
        'intento',
    )


def _total_items_datos(datos):
    """Ítems que aporta un bloque congelado (una relación puede aportar varios)."""
    datos = datos or {}
    if datos.get('parte') == 1:
        return len(datos.get('relaciones') or [])
    preguntas = datos.get('preguntas') or []
    return len(preguntas) if preguntas else 1


def _es_evaluable(datos):
    """Las consignas abiertas se califican aparte y no entran al desglose."""
    return (datos or {}).get('tipo') != 'consigna_escrita'


def _items_de(presentaciones, area_id=None, parte=None):
    """Bloques evaluables de los intentos, con su criterio y respuesta (si existe).

    Se recorren los bloques congelados (`PresentacionPregunta`) en lugar de las
    respuestas: un intento finalizado puede tener bloques sin responder y esos
    ítems deben seguir contando en el denominador, igual que en `puntaje`.
    """
    ids = [presentacion.id for presentacion in presentaciones]
    if not ids:
        return []

    respuestas = {
        respuesta.pregunta_id: respuesta
        for respuesta in RespuestaPresentacion.objects.filter(presentacion_id__in=ids)
    }
    bloques = PresentacionPregunta.objects.filter(
        presentacion_id__in=ids,
    ).select_related(
        'presentacion',
        'presentacion__estudiante',
        'contenido__area',
        'contenido__competencia',
        'contenido__afirmacion',
    )
    if area_id is not None:
        bloques = bloques.filter(contenido__area_id=area_id)
    if parte is not None:
        bloques = bloques.filter(contenido__parte=parte)

    items = []
    for bloque in bloques:
        if not _es_evaluable(bloque.datos):
            continue
        respuesta = respuestas.get(bloque.id)
        items.append(
            {
                'presentacion': bloque.presentacion,
                'contenido': bloque.contenido,
                'correctas': 0 if respuesta is None else respuesta.correctas,
                'total_items': (
                    respuesta.total_items
                    if respuesta is not None
                    else _total_items_datos(bloque.datos)
                ),
            }
        )
    return items


def _acumulador():
    return {'aciertos': 0, 'total_preguntas': 0, 'estudiantes': set()}


def _sumar(acumulador, item):
    aciertos = 0 if item['presentacion'].anulada else item['correctas']
    acumulador['aciertos'] += aciertos
    acumulador['total_preguntas'] += item['total_items']
    acumulador['estudiantes'].add(item['presentacion'].estudiante_id)


def _fila_desglose(acumulador):
    return {
        'aciertos': acumulador['aciertos'],
        'total_preguntas': acumulador['total_preguntas'],
        'porcentaje_acierto': _porcentaje(
            acumulador['aciertos'],
            acumulador['total_preguntas'],
        ),
        'total_estudiantes': len(acumulador['estudiantes']),
    }


def _ordenar_desglose(filas, campo):
    """Ordena de menor a mayor acierto y deja al final los grupos sin datos."""
    filas.sort(
        key=lambda fila: (
            fila['total_preguntas'] == 0,
            fila['porcentaje_acierto'],
            fila[campo]['nombre'].lower(),
        )
    )
    return filas


def _por_area(items):
    acumulados = {}
    for item in items:
        area = item['contenido'].area
        acumulador = acumulados.setdefault(area.id, {'area': area, **_acumulador()})
        _sumar(acumulador, item)
    filas = [
        {'area': _area_ref(acumulador['area']), **_fila_desglose(acumulador)}
        for acumulador in acumulados.values()
    ]
    return _ordenar_desglose(filas, 'area')


def _por_parte(items, parte=None):
    """Desempeño por parte del examen de Inglés (1 a 7).

    Es el desglose propio del área: sustituye a competencia/afirmación, que en
    Inglés no existen. `parte` restringe el resultado a una sola parte.
    """
    acumulados = {}
    for item in items:
        numero = item['contenido'].parte
        if numero is None:
            continue
        if parte is not None and numero != parte:
            continue
        acumulador = acumulados.setdefault(numero, {**_acumulador()})
        _sumar(acumulador, item)

    filas = [
        {'parte': _parte_ref(numero), **_fila_desglose(acumulador)}
        for numero, acumulador in acumulados.items()
    ]
    return _ordenar_desglose(filas, 'parte')


def _por_competencia(items, competencia, afirmacion):
    filtro_id = None
    if competencia is not None:
        filtro_id = competencia.id
    elif afirmacion is not None:
        filtro_id = afirmacion.competencia_id

    acumulados = {}
    for item in items:
        criterio = item['contenido'].competencia
        if criterio is None:
            continue
        if filtro_id is not None and criterio.id != filtro_id:
            continue
        acumulador = acumulados.setdefault(
            criterio.id,
            {'competencia': criterio, 'area': criterio.area, **_acumulador()},
        )
        _sumar(acumulador, item)

    filas = [
        {
            'competencia': _referencia(acumulador['competencia']),
            'area': _area_ref(acumulador['area']),
            **_fila_desglose(acumulador),
        }
        for acumulador in acumulados.values()
    ]
    return _ordenar_desglose(filas, 'competencia')


def _por_afirmacion(items, competencia, afirmacion):
    acumulados = {}
    for item in items:
        criterio = item['contenido'].afirmacion
        if criterio is None:
            continue
        if afirmacion is not None and criterio.id != afirmacion.id:
            continue
        if afirmacion is None and competencia is not None and criterio.competencia_id != competencia.id:
            continue
        acumulador = acumulados.setdefault(
            criterio.id,
            {
                'afirmacion': criterio,
                'competencia': criterio.competencia,
                'area': criterio.competencia.area,
                **_acumulador(),
            },
        )
        _sumar(acumulador, item)

    filas = [
        {
            'afirmacion': _referencia(acumulador['afirmacion']),
            'competencia': _referencia(acumulador['competencia']),
            'area': _area_ref(acumulador['area']),
            **_fila_desglose(acumulador),
        }
        for acumulador in acumulados.values()
    ]
    return _ordenar_desglose(filas, 'afirmacion')


def _focos_bajos(por_area, por_competencia, por_afirmacion, por_parte=None):
    """Los criterios con menor porcentaje de acierto, con foco académico."""
    candidatos = []
    for fila in por_competencia:
        if fila['total_preguntas'] == 0:
            continue
        candidatos.append(
            {
                'tipo': 'competencia',
                'id': fila['competencia']['id'],
                'nombre': fila['competencia']['nombre'],
                'porcentaje_acierto': fila['porcentaje_acierto'],
                'total_preguntas': fila['total_preguntas'],
            }
        )
    for fila in por_afirmacion:
        if fila['total_preguntas'] == 0:
            continue
        candidatos.append(
            {
                'tipo': 'afirmacion',
                'id': fila['afirmacion']['id'],
                'nombre': fila['afirmacion']['nombre'],
                'porcentaje_acierto': fila['porcentaje_acierto'],
                'total_preguntas': fila['total_preguntas'],
            }
        )
    for fila in por_parte or []:
        if fila['total_preguntas'] == 0:
            continue
        candidatos.append(
            {
                'tipo': 'parte',
                'id': fila['parte']['numero'],
                'nombre': fila['parte']['nombre'],
                'porcentaje_acierto': fila['porcentaje_acierto'],
                'total_preguntas': fila['total_preguntas'],
            }
        )
    if not candidatos:
        for fila in por_area:
            if fila['total_preguntas'] == 0:
                continue
            candidatos.append(
                {
                    'tipo': 'area',
                    'id': fila['area']['id'],
                    'nombre': fila['area']['nombre'],
                    'porcentaje_acierto': fila['porcentaje_acierto'],
                    'total_preguntas': fila['total_preguntas'],
                }
            )
    candidatos.sort(
        key=lambda fila: (
            fila['porcentaje_acierto'],
            -fila['total_preguntas'],
            fila['nombre'].lower(),
        )
    )
    return candidatos[:5]


def _resumen(presentaciones, items):
    puntajes = [_puntaje_efectivo(presentacion) for presentacion in presentaciones]
    calificaciones = [round(puntaje / 20, 2) for puntaje in puntajes]
    aciertos = sum(
        0 if item['presentacion'].anulada else item['correctas']
        for item in items
    )
    total_preguntas = sum(item['total_items'] for item in items)
    aprobados = sum(1 for calificacion in calificaciones if calificacion >= 3.0)
    programas = {
        perfil.programa_id
        for perfil in (
            _perfil_academico(presentacion.estudiante)
            for presentacion in presentaciones
        )
        if perfil is not None and perfil.programa_id is not None
    }
    return {
        'total_estudiantes': len({p.estudiante_id for p in presentaciones}),
        'total_intentos': len(presentaciones),
        'total_cursos': len({p.simulacro.curso_id for p in presentaciones}),
        'total_programas': len(programas),
        'total_preguntas': total_preguntas,
        'aciertos': aciertos,
        'porcentaje_acierto': _porcentaje(aciertos, total_preguntas),
        'promedio_puntaje': _promedio(puntajes),
        'promedio_calificacion': _promedio(calificaciones),
        'aprobados': aprobados,
        'tasa_aprobacion': _porcentaje(aprobados, len(calificaciones)),
    }


def _distribucion_calificaciones(presentaciones):
    rangos = [
        ('0.0 - 2.9', lambda nota: nota < 3.0),
        ('3.0 - 3.9', lambda nota: 3.0 <= nota < 4.0),
        ('4.0 - 4.5', lambda nota: 4.0 <= nota < 4.6),
        ('4.6 - 5.0', lambda nota: nota >= 4.6),
    ]
    calificaciones = [
        round(_puntaje_efectivo(presentacion) / 20, 2)
        for presentacion in presentaciones
    ]
    total = len(calificaciones)
    filas = []
    for etiqueta, condicion in rangos:
        cantidad = sum(1 for calificacion in calificaciones if condicion(calificacion))
        filas.append(
            {
                'rango': etiqueta,
                'cantidad': cantidad,
                'porcentaje': _porcentaje(cantidad, total),
            }
        )
    return filas


def _resultado_individual(presentacion):
    puntaje = _puntaje_efectivo(presentacion)
    calificacion = round(puntaje / 20, 2)
    aciertos = 0 if presentacion.anulada else presentacion.correctas
    total = presentacion.total_evaluables
    return {
        'estudiante': {
            'id': presentacion.estudiante_id,
            'nombre_completo': _nombre_completo(presentacion.estudiante),
            'email': presentacion.estudiante.email,
        },
        'curso': _curso_ref(presentacion.simulacro.curso),
        'simulacro': _simulacro_ref(presentacion.simulacro),
        'intento': presentacion.intento,
        'puntaje': round(puntaje, 2),
        'calificacion': calificacion,
        'correctas': presentacion.correctas,
        'aciertos': aciertos,
        'total_evaluables': total,
        'total_preguntas': total,
        'porcentaje_acierto': _porcentaje(aciertos, total),
        'aprobado': calificacion >= 3.0,
        'anulada': presentacion.anulada,
        'finalizada_en': presentacion.finalizada_en,
    }


def _metricas_presentaciones(presentaciones):
    puntajes = [_puntaje_efectivo(presentacion) for presentacion in presentaciones]
    calificaciones = [round(puntaje / 20, 2) for puntaje in puntajes]
    aprobados = sum(1 for calificacion in calificaciones if calificacion >= 3.0)
    aciertos = sum(
        0 if presentacion.anulada else presentacion.correctas
        for presentacion in presentaciones
    )
    total_evaluables = sum(
        presentacion.total_evaluables for presentacion in presentaciones
    )
    return {
        'total_estudiantes': len({p.estudiante_id for p in presentaciones}),
        'total_intentos': len(presentaciones),
        'promedio_puntaje': _promedio(puntajes),
        'promedio_calificacion': _promedio(calificaciones),
        'porcentaje_acierto': _porcentaje(aciertos, total_evaluables),
        'aprobados': aprobados,
        'tasa_aprobacion': _porcentaje(aprobados, len(calificaciones)),
    }


def _por_curso(presentaciones):
    grupos = {}
    for presentacion in presentaciones:
        curso = presentacion.simulacro.curso
        grupo = grupos.setdefault(curso.id, {'curso': curso, 'presentaciones': []})
        grupo['presentaciones'].append(presentacion)
    filas = [
        {
            'curso': _curso_ref(grupo['curso']),
            **_metricas_presentaciones(grupo['presentaciones']),
        }
        for grupo in grupos.values()
    ]
    filas.sort(
        key=lambda fila: (
            -fila['promedio_calificacion'],
            fila['curso']['nombre'].lower(),
        )
    )
    return filas


def _por_programa(presentaciones):
    grupos = {}
    for presentacion in presentaciones:
        programa = _programa_de(presentacion.estudiante)
        if programa is None:
            continue
        grupo = grupos.setdefault(programa.id, {'programa': programa, 'presentaciones': []})
        grupo['presentaciones'].append(presentacion)
    filas = [
        {
            'programa': _programa_ref(grupo['programa']),
            **_metricas_presentaciones(grupo['presentaciones']),
        }
        for grupo in grupos.values()
    ]
    filas.sort(
        key=lambda fila: (
            -fila['promedio_calificacion'],
            fila['programa']['nombre'].lower(),
        )
    )
    return filas


def _por_periodo(presentaciones):
    grupos = {}
    for presentacion in presentaciones:
        periodo = periodo_de(presentacion.finalizada_en)
        if not periodo:
            continue
        grupo = grupos.setdefault(periodo, {'periodo': periodo, 'presentaciones': []})
        grupo['presentaciones'].append(presentacion)
    filas = [
        {
            'periodo': grupo['periodo'],
            **_metricas_presentaciones(grupo['presentaciones']),
        }
        for grupo in grupos.values()
    ]
    filas.sort(key=lambda fila: fila['periodo'])
    return filas


def _filtro(area, competencia, afirmacion, simulacro, programa, periodo, curso=None, parte=None):
    return {
        'curso': _curso_ref(curso) if curso is not None else None,
        'programa': _programa_ref(programa),
        'area': _area_ref(area) if area is not None else None,
        'competencia': _referencia(competencia),
        'afirmacion': _referencia(afirmacion),
        'parte': _parte_ref(parte),
        'simulacro': _simulacro_ref(simulacro),
        'periodo': periodo or None,
    }


def construir_analitica_curso(
    docente,
    curso_id,
    simulacro_id=None,
    periodo=None,
    competencia_id=None,
    afirmacion_id=None,
    area_id=None,
    parte=None,
):
    """Analítica de un curso del docente (HU-24.1/24.2).

    Devuelve resumen, distribución de calificaciones, resultados individuales y
    desgloses por área/competencia/afirmación (o por parte en Inglés), con los
    filtros de simulacro, periodo y criterio académico. El curso se valida
    contra el docente autenticado para impedir consultar cursos ajenos
    (HU-24.1.5).
    """
    curso = obtener_curso_docente(docente, curso_id)
    validar_area(curso, area_id)
    simulacro = resolver_simulacro(curso, simulacro_id)
    competencia = _resolver_competencia(curso.area, competencia_id)
    afirmacion = _resolver_afirmacion(curso.area, afirmacion_id, competencia)
    parte = _resolver_parte(parte, curso.area)

    base = _con_relaciones(
        _presentaciones_base().filter(simulacro__curso=curso)
    )

    queryset = base
    if simulacro is not None:
        queryset = queryset.filter(simulacro=simulacro)
    periodos = _periodos_disponibles(queryset)
    queryset = _aplicar_periodo(queryset, periodo)
    presentaciones = list(_filtrar_presentaciones(queryset))

    items = _items_de(presentaciones, area_id=curso.area_id)
    items_parte = (
        _items_de(presentaciones, area_id=curso.area_id, parte=parte)
        if parte is not None
        else items
    )
    por_area = _por_area(items)
    por_competencia = _por_competencia(items, competencia, afirmacion)
    por_afirmacion = _por_afirmacion(items, competencia, afirmacion)
    por_parte = _por_parte(items_parte, parte)

    return {
        'curso': _curso_ref(curso),
        'filtro': _filtro(
            area=curso.area,
            competencia=competencia,
            afirmacion=afirmacion,
            parte=parte,
            simulacro=simulacro,
            programa=None,
            periodo=periodo,
            curso=None,
        ),
        'periodos_disponibles': periodos,
        'partes_disponibles': _partes_disponibles(curso.area, simulacro),
        'resumen': _resumen(presentaciones, items),
        'distribucion_calificaciones': _distribucion_calificaciones(presentaciones),
        'resultados_individuales': [
            _resultado_individual(presentacion) for presentacion in presentaciones
        ],
        'por_area': por_area,
        'por_competencia': por_competencia,
        'por_afirmacion': por_afirmacion,
        'por_parte': por_parte,
        'focos_bajos': _focos_bajos(por_area, por_competencia, por_afirmacion, por_parte),
    }


def _resolver_area_institucional(area_id):
    if area_id is None:
        return None
    area = AreaSaberPro.objects.filter(id=area_id).first()
    if area is None:
        raise AreaNoCorrespondeError('El área indicada no existe.')
    return area


def _competencia_institucional(competencia_id):
    if competencia_id is None:
        return None
    competencia = (
        CompetenciaSaberPro.objects.filter(id=competencia_id)
        .select_related('area')
        .first()
    )
    if competencia is None:
        raise CompetenciaNoEncontradaError('La competencia indicada no existe.')
    return competencia


def _afirmacion_institucional(afirmacion_id, competencia):
    if afirmacion_id is None:
        return None
    afirmacion = (
        AfirmacionSaberPro.objects.filter(id=afirmacion_id)
        .select_related('competencia__area')
        .first()
    )
    if afirmacion is None:
        raise AfirmacionNoEncontradaError('La afirmación indicada no existe.')
    if competencia is not None and afirmacion.competencia_id != competencia.id:
        raise AfirmacionNoEncontradaError(
            'La afirmación indicada no pertenece a la competencia seleccionada.'
        )
    return afirmacion


def construir_analitica_institucional(
    curso_id=None,
    programa_id=None,
    area_id=None,
    competencia_id=None,
    afirmacion_id=None,
    periodo=None,
    parte=None,
):
    """Analítica consolidada de la institución (HU-24.3/24.4).

    Filtra por curso, carrera (programa académico), área, criterio y periodo;
    en Inglés el criterio es la parte del examen (1 a 7). Devuelve indicadores
    generales, distribución, desgloses académicos y comparativas por curso,
    carrera y periodo. No expone resultados individuales: la vista institucional
    está orientada a la toma de decisiones y evita la exposición innecesaria de
    datos personales (HU-24.4.6).
    """
    curso = None
    if curso_id is not None:
        curso = (
            CursoSaberPro.objects.filter(id=curso_id)
            .select_related('area')
            .first()
        )
        if curso is None:
            raise CursoNoEncontradoError('Curso Saber Pro no encontrado.')

    programa = None
    if programa_id is not None:
        programa = ProgramaAcademico.objects.filter(id=programa_id).first()
        if programa is None:
            raise ProgramaNoEncontradoError('Programa académico no encontrado.')

    competencia = _competencia_institucional(competencia_id)
    afirmacion = _afirmacion_institucional(afirmacion_id, competencia)
    area = _resolver_area_institucional(area_id)

    area_criterio = None
    if competencia is not None:
        area_criterio = competencia.area
    elif afirmacion is not None:
        area_criterio = afirmacion.competencia.area

    if area is None:
        area = area_criterio
    elif area_criterio is not None and area.id != area_criterio.id:
        raise AreaNoCorrespondeError(
            'El área indicada no corresponde al criterio seleccionado.'
        )

    if curso is not None:
        if area is not None and curso.area_id != area.id:
            raise AreaNoCorrespondeError(
                'El área indicada no corresponde al curso seleccionado.'
            )
        area = curso.area

    if parte is not None and area is None:
        area = AreaSaberPro.objects.filter(nombre=AREA_PARTES).first()
        if area is None:
            raise ParteNoCorrespondeError(
                'El área de Inglés no está configurada en el sistema.'
            )
    parte = _resolver_parte(parte, area)

    base = _con_relaciones(_presentaciones_base())
    if curso is not None:
        base = base.filter(simulacro__curso=curso)
    if area is not None:
        base = base.filter(simulacro__curso__area=area)
    if programa is not None:
        base = base.filter(estudiante__perfil_academico__programa=programa)

    periodos = _periodos_disponibles(base)
    queryset = _aplicar_periodo(base, periodo)
    presentaciones = list(_filtrar_presentaciones(queryset))

    items = _items_de(presentaciones, area_id=area.id if area is not None else None)
    items_parte = (
        _items_de(
            presentaciones,
            area_id=area.id if area is not None else None,
            parte=parte,
        )
        if parte is not None
        else items
    )
    por_area = _por_area(items)
    por_competencia = _por_competencia(items, competencia, afirmacion)
    por_afirmacion = _por_afirmacion(items, competencia, afirmacion)
    por_parte = _por_parte(items_parte, parte)

    return {
        'filtro': _filtro(
            area=area,
            competencia=competencia,
            afirmacion=afirmacion,
            parte=parte,
            simulacro=None,
            programa=programa,
            periodo=periodo,
            curso=curso,
        ),
        'periodos_disponibles': periodos,
        'partes_disponibles': _partes_disponibles(area),
        'resumen': _resumen(presentaciones, items),
        'distribucion_calificaciones': _distribucion_calificaciones(presentaciones),
        'por_area': por_area,
        'por_competencia': por_competencia,
        'por_afirmacion': por_afirmacion,
        'por_parte': por_parte,
        'por_curso': _por_curso(presentaciones),
        'por_programa': _por_programa(presentaciones),
        'por_periodo': _por_periodo(presentaciones),
        'focos_bajos': _focos_bajos(por_area, por_competencia, por_afirmacion, por_parte),
    }
