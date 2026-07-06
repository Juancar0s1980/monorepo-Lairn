"""
Cliente del microservicio ML (Knowledge Tracing con BKT).

Reemplaza el heuristico simple (tasa = correctas/intentos) por la estimacion de
dominio del modelo BKT servido por el microservicio. Es RESILIENTE: si el
microservicio no responde o el concepto no esta en el vocabulario entrenado,
cae de vuelta al heuristico clasico para no romper el examen.

Estructura de `conceptos` (JSONField del ModeloConocimiento):
    {
      "<concepto>": {
        "intentos": int,
        "correctas": int,
        "nivel": 1|2|3,
        "secuencia": [0/1, ...],     # historial de aciertos (para BKT)
        "p_dominado": float|null      # ultima estimacion del ML (informativo)
      }
    }
"""

import requests
from django.conf import settings


def _nivel_heuristico(correctas: int, intentos: int) -> int:
    """Nivel por tasa de aciertos (respaldo cuando el ML no aplica)."""
    tasa = correctas / intentos if intentos else 0.0
    if tasa >= 0.8:
        return 3
    if tasa >= 0.5:
        return 2
    return 1


def actualizar_modelo_conocimiento_ml(conceptos: dict, concepto: str, es_correcta: bool) -> dict:
    """
    Registra la interaccion y recalcula el nivel de dominio.

    1) Actualiza contadores + secuencia del concepto (siempre).
    2) Pide al microservicio ML el nivel via BKT para los conceptos reconocidos.
    3) Si el ML falla o el concepto no se reconoce, usa el heuristico de respaldo.
    """
    # --- 1) Actualizacion local (independiente del ML) ---
    if concepto not in conceptos:
        conceptos[concepto] = {"intentos": 0, "correctas": 0, "nivel": 2, "secuencia": []}
    c = conceptos[concepto]
    c.setdefault("secuencia", [])
    c["intentos"] += 1
    if es_correcta:
        c["correctas"] += 1
    c["secuencia"].append(1 if es_correcta else 0)

    # --- 2) Intento con el microservicio ML ---
    url = getattr(settings, "ML_SERVICE_URL", "") or ""
    reconocido_actual = False
    if url:
        try:
            # Construimos la lista de interacciones desde las secuencias guardadas.
            # (BKT es independiente por skill, el orden entre conceptos no importa.)
            interacciones = [
                {"concepto": nombre, "correcto": bool(obs)}
                for nombre, datos in conceptos.items()
                for obs in datos.get("secuencia", [])
            ]
            respuesta = requests.post(
                f"{url.rstrip('/')}/predict",
                json={"interacciones": interacciones},
                timeout=3,
            )
            respuesta.raise_for_status()
            data = respuesta.json()

            for nombre, res in data.get("conceptos", {}).items():
                if nombre in conceptos and res.get("reconocido"):
                    conceptos[nombre]["nivel"] = res["nivel"]
                    conceptos[nombre]["p_dominado"] = res["p_dominado"]
                    if nombre == concepto:
                        reconocido_actual = True
        except requests.RequestException:
            # ML caido o lento: seguimos con el respaldo heuristico
            pass

    # --- 3) Respaldo heuristico para el concepto actual si el ML no lo cubrio ---
    if not reconocido_actual:
        c["nivel"] = _nivel_heuristico(c["correctas"], c["intentos"])

    return conceptos
