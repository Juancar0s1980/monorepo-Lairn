"""
Configuracion central del servicio (rutas, umbrales, metadatos).

Todo lo parametrizable vive aqui, leyendo variables de entorno con valores por
defecto sensatos, para no dispersar "numeros magicos" por el codigo.
"""

import os
from pathlib import Path

# Raiz del proyecto = microservicio_ml/ (dos niveles arriba de este archivo).
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


class Ajustes:
    """Ajustes del servicio. Se instancia una sola vez (abajo, como `ajustes`)."""

    # --- Identidad del servicio ---
    NOMBRE: str = "Microservicio ML Lairn - Knowledge Tracing"
    VERSION: str = "1.0.0"

    # --- Modelo que se sirve ---
    # Por defecto BKT sintetico (unico cuyo vocabulario mapea a examenes reales).
    NOMBRE_MODELO: str = os.getenv("ML_MODELO", "bkt_sintetico")

    # --- Rutas de artefactos ---
    DIR_ARTEFACTOS: Path = RAIZ_PROYECTO / "artefactos"

    # --- Umbrales de nivel de dominio (coinciden con el backend) ---
    UMBRAL_DOMINADO: float = float(os.getenv("ML_UMBRAL_DOMINADO", "0.80"))  # nivel 3
    UMBRAL_MEDIO: float = float(os.getenv("ML_UMBRAL_MEDIO", "0.50"))        # nivel 2

    @property
    def ruta_modelo(self) -> Path:
        """Ruta al model.pkl del modelo configurado."""
        return self.DIR_ARTEFACTOS / self.NOMBRE_MODELO / "model.pkl"

    @property
    def ruta_vocab(self) -> Path:
        """Ruta al mapa de conceptos concepto->skill."""
        return self.DIR_ARTEFACTOS / "concept_vocab.json"

    def nivel(self, mastery: float) -> int:
        """Traduce P(dominado) a nivel 1 (debil) / 2 (en desarrollo) / 3 (dominado)."""
        if mastery >= self.UMBRAL_DOMINADO:
            return 3
        if mastery >= self.UMBRAL_MEDIO:
            return 2
        return 1


# Instancia unica reutilizable en toda la app
ajustes = Ajustes()
