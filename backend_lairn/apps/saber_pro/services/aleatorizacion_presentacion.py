"""
Aleatorización de la presentación de simulacros Saber Pro (HU-22.3).

Cada intento debe ver las preguntas y las opciones en un orden distinto para
reducir el riesgo de fraude, sin alterar la calificación: las respuestas
correctas se conservan y la evaluación compara por texto, no por posición.

Reglas:

- Los bloques de un área estructurada se mezclan por intento. En Inglés se
  conserva el orden oficial de las 7 partes porque la estructura del examen es
  secuencial.
- Las opciones de cada pregunta se mezclan. En la parte 1 de Inglés también se
  mezclan las descripciones y el banco de palabras.
- En las partes 2 y 3 de Inglés (ítems autocontenidos) se mezclan las preguntas
  internas. En las partes 4 a 7 no se reordenan porque comparten un texto base
  con espacios numerados que dependen del orden.

La aleatorización ocurre al crear el snapshot del intento; a partir de ahí el
contenido queda congelado en `PresentacionPregunta.datos`.
"""

import copy
import random

from apps.saber_pro.services.catalogo_saber_pro import (
    ESTRUCTURA_PARTES,
    obtener_estructura_area,
)

# Generador independiente del estado global de `random`; se usa SystemRandom
# para que la secuencia no dependa de la semilla del proceso.
_ALEATORIO = random.SystemRandom()

# Partes de Inglés cuyas preguntas internas son autocontenidas y se pueden
# reordenar sin romper el texto base compartido de las partes 4 a 7.
PARTES_INGLES_REORDENABLES = (2, 3)


def construir_snapshots(simulacro, asignaciones) -> list[tuple]:
    """Devuelve pares `(asignación, snapshot)` listos para persistir.

    El snapshot es una copia profunda del contenido aprobado, ya aleatorizada
    para este intento. El par conserva la asignación original para guardar la
    relación con el banco (`PresentacionPregunta.contenido`).
    """
    pares = [
        (
            asignacion,
            _snapshot_contenido(asignacion.contenido, simulacro.limite_palabras),
        )
        for asignacion in asignaciones
    ]
    pares = _ordenar_bloques(pares, simulacro.curso.area)
    for _, snapshot in pares:
        _aleatorizar_snapshot(snapshot)
    return pares


def _snapshot_contenido(contenido, limite_palabras=None) -> dict:
    """Copia profunda del contenido necesaria para presentar y calificar."""
    return {
        'contenido_id': contenido.id,
        'tipo': contenido.tipo,
        'parte': contenido.parte,
        'tema': contenido.tema,
        'contexto': contenido.contexto,
        'enunciado': contenido.enunciado,
        'opciones': list(contenido.opciones or []),
        'respuesta_correcta': contenido.respuesta_correcta,
        'relaciones': copy.deepcopy(list(contenido.relaciones or [])),
        'preguntas': copy.deepcopy(list(contenido.preguntas or [])),
        'limite_palabras': limite_palabras,
    }


def _ordenar_bloques(pares, area) -> list[tuple]:
    """Mezcla los bloques, salvo en Inglés donde manda la estructura oficial."""
    if obtener_estructura_area(area) == ESTRUCTURA_PARTES:
        return sorted(
            pares,
            key=lambda par: (par[0].contenido.parte or 0, par[0].orden, par[0].id),
        )
    _ALEATORIO.shuffle(pares)
    return pares


def _aleatorizar_snapshot(snapshot: dict) -> None:
    """Aplica las mezclas que corresponden a la estructura del bloque."""
    _mezclar_opciones(snapshot)

    if snapshot.get('parte') == 1:
        _ALEATORIO.shuffle(snapshot['relaciones'])

    preguntas = snapshot.get('preguntas') or []
    for pregunta in preguntas:
        _mezclar_opciones(pregunta)

    if snapshot.get('parte') in PARTES_INGLES_REORDENABLES:
        _ALEATORIO.shuffle(preguntas)


def _mezclar_opciones(datos: dict) -> None:
    """Mezcla la lista de opciones de una pregunta, si tiene más de una."""
    opciones = datos.get('opciones')
    if isinstance(opciones, list) and len(opciones) > 1:
        _ALEATORIO.shuffle(opciones)
