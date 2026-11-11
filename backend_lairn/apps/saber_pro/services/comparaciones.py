"""
Servicios de comparación de desempeño del módulo Saber Pro (HU-23).

Centraliza las reglas de comparación para que las vistas del docente y del
estudiante compartan exactamente el mismo cálculo:

- `construir_ranking`: listado nominal de un curso para el docente. Cuando se
  filtra por simulacro usa el mejor intento elegible de cada estudiante; cuando
  se compara el curso completo (por área) promedia los mejores intentos de cada
  simulacro, para que un estudiante con más intentos no quede favorecido.
- `calcular_desempeno`: devuelve solo los agregados del estudiante autenticado
  (puntaje, calificación, percentil y cantidad de compañeros). Nunca expone
  nombres, correos ni posiciones individuales de otros estudiantes (HU-23.4).
- `resolver_curso_estudiante`: resuelve el curso a comparar a partir de la
  inscripción del estudiante y de los filtros `curso_id`, `area_id` y
  `simulacro_id`, rechazando combinaciones incoherentes.
- `opciones_desempeno_estudiante`: cursos inscritos y simulacros presentados
  con resultados calificados: la base de los filtros de "Mi desempeño", para
  que el estudiante solo pueda compararse donde tiene resultados.

Solo se consideran intentos `finalizada` y sin revisión pendiente. Así un
intento con consignas abiertas aún no calificadas no altera el ranking ni el
percentil con un puntaje parcial.
"""

from django.db.models import Q

from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro
from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.simulacro import Simulacro


class ErrorComparacionSaberPro(Exception):
    """Base de los errores de dominio de la comparación de desempeño (HU-23)."""

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class CursoNoEncontradoError(ErrorComparacionSaberPro):
    """El curso no existe o no pertenece al usuario autenticado."""


class SimulacroNoEncontradoError(ErrorComparacionSaberPro):
    """El simulacro no existe o no pertenece al curso seleccionado."""


class AreaNoCorrespondeError(ErrorComparacionSaberPro):
    """El área indicada no coincide con el área del curso seleccionado."""


def _presentaciones_elegibles(curso, simulacro=None):
    """Intentos finalizados y calificados del curso (opcionalmente de un simulacro).

    `requiere_revision` sin `calificacion_docente` significa que el intento aún
    espera la revisión de consignas abiertas; se excluye para no comparar
    puntajes automáticos parciales con intentos ya completos.
    """
    queryset = PresentacionSimulacro.objects.filter(
        simulacro__curso=curso,
        estado='finalizada',
    ).filter(Q(requiere_revision=False) | Q(calificacion_docente__isnull=False))

    if simulacro is not None:
        queryset = queryset.filter(simulacro=simulacro)

    return queryset.select_related('estudiante', 'simulacro')


def _agrupar_por_estudiante(presentaciones):
    """Agrupa los intentos por estudiante conservando su mejor puntaje por simulacro."""
    grupos = {}

    for presentacion in presentaciones:
        grupo = grupos.get(presentacion.estudiante_id)
        if grupo is None:
            grupo = grupos[presentacion.estudiante_id] = {
                'estudiante': presentacion.estudiante,
                'mejores_por_simulacro': {},
                'intentos_considerados': 0,
            }

        grupo['intentos_considerados'] += 1
        anterior = grupo['mejores_por_simulacro'].get(presentacion.simulacro_id)
        if anterior is None or presentacion.puntaje > anterior:
            grupo['mejores_por_simulacro'][presentacion.simulacro_id] = presentacion.puntaje

    return grupos


def _puntaje_comparado(grupo, por_simulacro):
    """Puntaje comparable de un estudiante según el tipo de filtro.

    Con un simulacro concreto se usa su mejor intento. Al comparar todo el
    curso se promedian los mejores intentos de cada simulacro: así el resultado
    no depende de cuántas veces practicó cada estudiante.
    """
    puntajes = list(grupo['mejores_por_simulacro'].values())
    if not puntajes:
        return None
    if por_simulacro:
        return puntajes[0]
    return sum(puntajes) / len(puntajes)


def _nombre_completo(estudiante):
    return f'{estudiante.first_name} {estudiante.first_last_name}'.strip()


def _filas_ranking(grupos, por_simulacro):
    """Construye las filas ordenadas y con posición competitiva (empates comparten puesto)."""
    filas = []

    for grupo in grupos.values():
        puntaje = _puntaje_comparado(grupo, por_simulacro)
        if puntaje is None:
            continue

        estudiante = grupo['estudiante']
        filas.append(
            {
                'estudiante': {
                    'id': estudiante.id,
                    'nombre_completo': _nombre_completo(estudiante),
                    'email': estudiante.email,
                },
                'puntaje': round(puntaje, 2),
                'calificacion': round(puntaje / 20, 2),
                'intentos_considerados': grupo['intentos_considerados'],
                'simulacros_considerados': len(grupo['mejores_por_simulacro']),
            }
        )

    filas.sort(
        key=lambda fila: (
            -fila['puntaje'],
            fila['estudiante']['nombre_completo'].lower(),
            fila['estudiante']['id'],
        )
    )

    posicion = 0
    puntaje_anterior = None
    for indice, fila in enumerate(filas, start=1):
        if puntaje_anterior is None or fila['puntaje'] != puntaje_anterior:
            posicion = indice
        fila['posicion'] = posicion
        puntaje_anterior = fila['puntaje']

    return filas


def construir_ranking(curso, simulacro=None):
    """Devuelve el listado nominal ordenado del curso para el docente (HU-23.1/23.2)."""
    presentaciones = list(_presentaciones_elegibles(curso, simulacro))
    grupos = _agrupar_por_estudiante(presentaciones)
    return _filas_ranking(grupos, por_simulacro=simulacro is not None)


def calcular_percentil(puntaje, puntajes):
    """Porcentaje de estudiantes del curso con puntaje estrictamente menor.

    El denominador incluye al propio estudiante para expresar "superaste al X%
    del curso". Los empates no cuentan como superados. Con un solo estudiante
    no hay comparación posible y se devuelve 0.
    """
    total = len(puntajes)
    if total <= 1:
        return 0
    superados = sum(1 for valor in puntajes if valor < puntaje)
    return round(superados / total * 100)


def _etiqueta_filtro(curso, simulacro):
    if simulacro is not None:
        titulo = simulacro.titulo or f'Simulacro #{simulacro.id}'
        return f'el simulacro «{titulo}»'
    return f'el área {curso.area.nombre}'


def calcular_desempeno(estudiante, curso, simulacro=None):
    """Agregados del estudiante frente a su curso, sin revelar datos de terceros.

    Devuelve un diccionario con `tiene_resultados`, `hay_comparacion`,
    `total_estudiantes`, `percentil`, `mensaje`, `mi_puntaje`,
    `mi_calificacion`, `mis_intentos_considerados` y
    `mis_simulacros_considerados` (la vista lo valida con su serializador).
    """
    presentaciones = list(_presentaciones_elegibles(curso, simulacro))
    grupos = _agrupar_por_estudiante(presentaciones)
    filas = _filas_ranking(grupos, por_simulacro=simulacro is not None)
    etiqueta = _etiqueta_filtro(curso, simulacro)

    propia = next(
        (fila for fila in filas if fila['estudiante']['id'] == estudiante.id),
        None,
    )

    if propia is None:
        return {
            'tiene_resultados': False,
            'hay_comparacion': False,
            'total_estudiantes': len(filas),
            'percentil': None,
            'mensaje': (
                f'Aún no tienes intentos calificados en {etiqueta}. '
                'Cuando termines un simulacro y sea calificado, verás tu comparación.'
            ),
            'mi_puntaje': None,
            'mi_calificacion': None,
            'mis_intentos_considerados': 0,
            'mis_simulacros_considerados': 0,
        }

    grupo = grupos[estudiante.id]
    puntajes = [fila['puntaje'] for fila in filas]
    hay_comparacion = len(puntajes) > 1
    percentil = calcular_percentil(propia['puntaje'], puntajes)

    if not hay_comparacion:
        mensaje = (
            f'Aún no hay otros estudiantes con resultados en {etiqueta} para '
            'comparar tu desempeño. Tu resultado ya quedó registrado.'
        )
    elif percentil == 0:
        mensaje = (
            f'Tu resultado aún no supera al de otros estudiantes en {etiqueta}. '
            'Sigue practicando para mejorar tu comparación.'
        )
    else:
        mensaje = (
            f'Superaste al {percentil}% de los estudiantes de tu curso en {etiqueta}.'
        )

    return {
        'tiene_resultados': True,
        'hay_comparacion': hay_comparacion,
        'total_estudiantes': len(filas),
        'percentil': percentil,
        'mensaje': mensaje,
        'mi_puntaje': propia['puntaje'],
        'mi_calificacion': propia['calificacion'],
        'mis_intentos_considerados': grupo['intentos_considerados'],
        'mis_simulacros_considerados': len(grupo['mejores_por_simulacro']),
    }


def obtener_curso_docente(docente, curso_id):
    """Curso del docente autenticado o error de dominio si no le pertenece."""
    curso = (
        CursoSaberPro.objects.filter(id=curso_id, docente=docente)
        .select_related('area')
        .first()
    )
    if curso is None:
        raise CursoNoEncontradoError('Curso Saber Pro no encontrado.')
    return curso


def resolver_simulacro(curso, simulacro_id):
    """Simulacro del curso indicado o error de dominio si no pertenece al curso."""
    if simulacro_id is None:
        return None

    simulacro = Simulacro.objects.filter(id=simulacro_id, curso=curso).first()
    if simulacro is None:
        raise SimulacroNoEncontradoError('Simulacro no encontrado en este curso.')
    return simulacro


def validar_area(curso, area_id):
    """Rechaza un filtro de área que no corresponde al área fija del curso."""
    if area_id is not None and curso.area_id != area_id:
        raise AreaNoCorrespondeError('El área indicada no corresponde al curso seleccionado.')


def resolver_curso_estudiante(estudiante, curso_id=None, area_id=None, simulacro_id=None):
    """Resuelve el curso y simulacro a comparar para el estudiante autenticado.

    Prioridad: un simulacro concreto (y su curso) manda sobre `curso_id`, que a
    su vez manda sobre `area_id`. Si no se envía ningún filtro se toma el primer
    curso inscrito. Se valida que el curso pertenezca al estudiante y que el
    área (si se envía) coincida con la del curso.
    """
    inscripciones = InscripcionCursoSaberPro.objects.filter(
        estudiante=estudiante,
    ).select_related('curso__area')

    if simulacro_id is not None:
        simulacro = (
            Simulacro.objects.filter(id=simulacro_id)
            .select_related('curso__area')
            .first()
        )
        if simulacro is None:
            raise SimulacroNoEncontradoError('Simulacro no encontrado.')
        if not inscripciones.filter(curso=simulacro.curso).exists():
            raise CursoNoEncontradoError(
                'El simulacro no pertenece a un curso en el que estés inscrito.'
            )
        validar_area(simulacro.curso, area_id)
        return simulacro.curso, simulacro

    if curso_id is not None:
        inscripcion = inscripciones.filter(curso_id=curso_id).first()
        if inscripcion is None:
            raise CursoNoEncontradoError(
                'No estás inscrito en el curso Saber Pro indicado.'
            )
        validar_area(inscripcion.curso, area_id)
        return inscripcion.curso, None

    if area_id is not None:
        inscripcion = (
            inscripciones.filter(curso__area_id=area_id)
            .order_by('curso__nombre', 'curso_id')
            .first()
        )
        if inscripcion is None:
            raise CursoNoEncontradoError(
                'No estás inscrito en un curso Saber Pro de esa área.'
            )
        return inscripcion.curso, None

    inscripcion = inscripciones.order_by('curso__nombre', 'curso_id').first()
    if inscripcion is None:
        raise CursoNoEncontradoError('Aún no perteneces a ningún curso Saber Pro.')
    return inscripcion.curso, None


def opciones_desempeno_estudiante(estudiante):
    """Cursos y simulacros comparables por el estudiante, para sus filtros.

    Base del listado de filtros de "Mi desempeño": solo se ofrecen los cursos
    inscritos donde el estudiante tiene al menos un intento elegible y, dentro
    de cada curso, solo los simulacros que presentó y ya están calificados (con
    el mismo criterio de `_presentaciones_elegibles`, para que el filtro nunca
    ofrezca una combinación sin resultados propios).

    Devuelve una lista de diccionarios `{'curso': CursoSaberPro, 'simulacros':
    [Simulacro, ...]}`: cursos ordenados por nombre y simulacros del más
    reciente al más antiguo (el orden por defecto del modelo).
    """
    ids_cursos_inscritos = set(
        InscripcionCursoSaberPro.objects.filter(estudiante=estudiante).values_list(
            'curso_id', flat=True
        )
    )
    presentaciones = (
        PresentacionSimulacro.objects.filter(
            estudiante=estudiante,
            estado='finalizada',
        )
        .filter(Q(requiere_revision=False) | Q(calificacion_docente__isnull=False))
        .select_related('simulacro__curso__area')
        .order_by(
            'simulacro__curso__nombre',
            'simulacro__curso__id',
            '-simulacro__creado_en',
            '-simulacro__id',
        )
    )

    opciones = []
    indice_por_curso = {}
    ids_simulacros_por_curso = {}
    for presentacion in presentaciones:
        curso = presentacion.simulacro.curso
        if curso.id not in ids_cursos_inscritos:
            continue

        opcion = indice_por_curso.get(curso.id)
        if opcion is None:
            opcion = indice_por_curso[curso.id] = {'curso': curso, 'simulacros': []}
            ids_simulacros_por_curso[curso.id] = set()
            opciones.append(opcion)

        ids_vistos = ids_simulacros_por_curso[curso.id]
        if presentacion.simulacro_id not in ids_vistos:
            ids_vistos.add(presentacion.simulacro_id)
            opcion['simulacros'].append(presentacion.simulacro)

    return opciones
