"""
Preprocesamiento: traduce conceptos en lenguaje natural (los que genera GPT en
el backend, ej. "Derivada del seno") a los skills fijos con que se entreno el
modelo BKT sintetico: derivada_seno, derivada_coseno, regla_cadena.

Si un concepto no se puede mapear devuelve None y el backend aplica su
heuristica de respaldo (no rompe el flujo).
"""

import json
import unicodedata
from pathlib import Path

# Mapa de respaldo por si concept_vocab.json no existe o esta vacio.
# OJO con el orden: "coseno" CONTIENE "seno" como subcadena, por eso se evalua
# regla_cadena y derivada_coseno ANTES que derivada_seno.
_VOCAB_POR_DEFECTO = {
    "orden_evaluacion": ["regla_cadena", "derivada_coseno", "derivada_seno"],
    "mapa": {
        "regla_cadena": ["regla de la cadena", "regla cadena", "cadena",
                          "funcion compuesta", "funciones compuestas", "compuesta",
                          "composicion de funciones"],
        "derivada_coseno": ["derivada del coseno", "derivada de coseno", "coseno", "cos"],
        "derivada_seno": ["derivada del seno", "derivada de seno", "seno", "sen", "sin"],
    },
}


def _normalizar(texto: str) -> str:
    """Minusculas + sin acentos + sin espacios sobrantes, para comparar robusto."""
    texto = (texto or "").lower().strip()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto


def cargar_vocab(ruta) -> dict:
    """
    Carga concept_vocab.json. Si esta vacio o falla, usa el vocab por defecto.
    Devuelve siempre un dict con claves 'orden_evaluacion' y 'mapa'.
    """
    try:
        contenido = Path(ruta).read_text(encoding="utf-8").strip()
        if contenido:
            data = json.loads(contenido)
            orden = data.get("orden_evaluacion") or data.get("orden")
            mapa = data.get("mapa")
            if orden and mapa:
                return {"orden_evaluacion": orden, "mapa": mapa}
    except Exception:
        pass
    return _VOCAB_POR_DEFECTO


def mapear_concepto(concepto: str, vocab: dict):
    """
    Traduce un concepto en lenguaje natural al skill entrenado correspondiente.

    Devuelve el nombre del skill o None si no se reconoce.
    """
    n = _normalizar(concepto)
    if not n:
        return None
    orden = vocab.get("orden_evaluacion", _VOCAB_POR_DEFECTO["orden_evaluacion"])
    mapa = vocab.get("mapa", _VOCAB_POR_DEFECTO["mapa"])
    for skill in orden:
        for palabra_clave in mapa.get(skill, []):
            if _normalizar(palabra_clave) in n:
                return skill
    return None
