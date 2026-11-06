"""
Reporte ejecutivo institucional (HU-11.1 / 11.2), ampliado con filtros (ADR-011).

Fuente: evaluaciones formales realizadas (vía `servicio_analitica_ra.notas`).
  - Cuestionario: cada intento ENVIADO y no anulado por fraude aporta su nota
    (0-5). Por materia, la nota se recalcula solo con las preguntas de esa
    asignatura (y de los RA/competencias filtrados).
  - Tarea: cada entrega CALIFICADA de la tarea evaluada aporta su nota.

Indicadores por nivel (institución → programa → materia):
  estudiantes evaluados, resultados registrados, puntaje promedio,
  desviación estándar, distribución en rangos de 1 punto y cuántos quedan
  por encima / por debajo de la media (HU-11.1).
La analítica de RA (logro, cobertura, participación, mapas, tendencia) vive en
`servicio_analitica_ra` y se añade a la misma respuesta bajo `analitica`.
"""

from collections import defaultdict
from statistics import mean, pstdev

from .servicio_analitica_ra import Filtros, _integridad, cerrar_vencidos, notas

RANGOS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]


def _resultados(filtros: Filtros):
    """Lista de resultados: {estudiante, programa, asignatura, nota}."""
    cerrar_vencidos()
    return notas(filtros)


def _indicadores(filas) -> dict:
    notas_ = [f['nota'] for f in filas]
    if not notas_:
        return {'estudiantes': 0, 'resultados': 0, 'promedio': None, 'desviacion': None,
                'por_encima': 0, 'por_debajo': 0, 'distribucion': [
                    {'rango': f'{a}–{b}', 'cantidad': 0} for a, b in RANGOS]}
    media = mean(notas_)
    distribucion = []
    for a, b in RANGOS:
        # El último rango incluye el 5.0.
        cantidad = sum(1 for n in notas_ if a <= n < b or (b == 5 and n == 5))
        distribucion.append({'rango': f'{a}–{b}', 'cantidad': cantidad})
    return {
        'estudiantes': len({f['estudiante'] for f in filas}),
        'resultados': len(notas_),
        'promedio': round(media, 2),
        'desviacion': round(pstdev(notas_), 2),
        'por_encima': sum(1 for n in notas_ if n > media),
        'por_debajo': sum(1 for n in notas_ if n < media),
        'distribucion': distribucion,
    }


def integridad(programa=None) -> dict:
    """Suspensiones, anulaciones y reactivaciones (ADR-010)."""
    return _integridad(Filtros(programa=programa.id if programa else None))


def reporte(programa=None, filtros: Filtros | None = None, filas=None) -> dict:
    """Nivel institucional (con desglose por programa) o de un programa (con desglose por materia)."""
    filtros = filtros or Filtros(programa=programa.id if programa else None)
    filas = _resultados(filtros) if filas is None else filas
    if programa is None:
        grupos = defaultdict(list)
        for f in filas:
            grupos[f['programa'].id].append(f)
        return {
            'nivel': 'institucion',
            'indicadores': _indicadores(filas),
            'integridad': _integridad(filtros),
            'desglose': sorted(
                ({'id': g[0]['programa'].id, 'codigo': g[0]['programa'].codigo, 'nombre': g[0]['programa'].nombre,
                  **_indicadores(g)} for g in grupos.values()),
                key=lambda d: d['nombre'],
            ),
        }
    del_programa = [f for f in filas if f['programa'].id == programa.id]
    grupos = defaultdict(list)
    for f in del_programa:
        grupos[f['asignatura'].id].append(f)
    return {
        'nivel': 'programa',
        'programa': {'id': programa.id, 'codigo': programa.codigo, 'nombre': programa.nombre},
        'indicadores': _indicadores(del_programa),
        'integridad': _integridad(filtros),
        'desglose': sorted(
            ({'id': g[0]['asignatura'].id, 'codigo': g[0]['asignatura'].codigo, 'nombre': g[0]['asignatura'].nombre,
              **_indicadores(g)} for g in grupos.values()),
            key=lambda d: d['nombre'],
        ),
    }
