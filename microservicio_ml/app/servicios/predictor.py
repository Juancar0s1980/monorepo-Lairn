"""
Predictor: carga el modelo BKT entrenado (artefactos/<modelo>/model.pkl) y
calcula el "mastery" (probabilidad de dominio) online.

El .pkl fue serializado con la clase ml.modelos.bkt.BKTModel, por eso se asegura
que la raiz del proyecto este en sys.path antes de deserializar.
"""

import pickle
import sys

from app.config import RAIZ_PROYECTO

# Aseguramos que 'import ml.modelos.bkt' funcione al deserializar el pickle.
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

# Constante para evitar divisiones por cero (igual que en ml/modelos/bkt.py).
EPS = 1e-12


class PredictorBKT:
    """Envuelve un BKTModel entrenado y calcula mastery por skill."""

    def __init__(self, ruta_modelo):
        with open(ruta_modelo, "rb") as f:
            self._modelo = pickle.load(f)
        # params_ = {skill: {p_init, p_learn, p_guess, p_slip}}
        self.params = dict(self._modelo.params_)
        self.skills = list(self.params.keys())

    def mastery(self, skill: str, secuencia: list) -> float:
        """
        P(dominado) tras observar la secuencia de respuestas (0/1) del skill,
        proyectada para la SIGUIENTE interaccion.
        """
        p = self.params[skill]
        p_l = p["p_init"]
        for obs in secuencia:
            p_correct = p_l * (1.0 - p["p_slip"]) + (1.0 - p_l) * p["p_guess"]
            if int(obs) == 1:
                num = p_l * (1.0 - p["p_slip"])
                den = p_correct + EPS
            else:
                num = p_l * p["p_slip"]
                den = (1.0 - p_correct) + EPS
            p_l_post = num / den
            p_l = p_l_post + (1.0 - p_l_post) * p["p_learn"]
        return float(p_l)

    def p_acierto(self, skill: str, p_dominado: float) -> float:
        """Probabilidad de acertar la siguiente pregunta dado P(dominado)."""
        p = self.params[skill]
        return float(p_dominado * (1.0 - p["p_slip"]) + (1.0 - p_dominado) * p["p_guess"])
