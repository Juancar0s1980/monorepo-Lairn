"""
Catalogo de modelos: lee los artefactos entrenados (config.json + metrics.json)
para exponer el estado de las redes (metricas, tamano del dataset, etc.).

Lo usa el endpoint /modelos, que a su vez alimenta el panel de "Redes
Neuronales" del administrador.
"""

import json
from pathlib import Path


def _leer_json(ruta: Path) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}


def listar_modelos(dir_artefactos: Path, modelo_activo: str) -> list[dict]:
    """
    Recorre las subcarpetas de artefactos/ y devuelve la ficha de cada modelo.

    Cada carpeta con un config.json cuenta como un modelo entrenado.
    """
    modelos = []
    if not dir_artefactos.exists():
        return modelos

    for sub in sorted(p for p in dir_artefactos.iterdir() if p.is_dir()):
        config = _leer_json(sub / "config.json")
        if not config:
            continue  # carpeta sin config -> no es un modelo valido
        metrics = _leer_json(sub / "metrics.json") or config.get("metricas", {})
        # Los datos del dataset estan a nivel raiz (modelos 'real') o anidados
        # bajo 'dataset' (modelos 'sintetico'). Soportamos ambas formas.
        dataset = config.get("dataset", {})
        conceptos = dataset.get("conceptos", [])
        modelos.append({
            "nombre": sub.name,
            "tipo": config.get("modelo", ""),
            "fuente": config.get("fuente") or dataset.get("fuente", ""),
            "n_estudiantes": config.get("n_estudiantes") or dataset.get("estudiantes_unicos"),
            "n_skills": config.get("n_skills") or (len(conceptos) or None),
            "metricas": {
                "auc": metrics.get("auc"),
                "accuracy": metrics.get("accuracy"),
                "f1": metrics.get("f1"),
                "rmse": metrics.get("rmse"),
            },
            "activo": sub.name == modelo_activo,
        })
    return modelos
