"""
Pruebas del servicio ML. Ejecutar desde microservicio_ml/ con:  pytest

Cubren lo esencial: mapeo de conceptos, monotonia del mastery y los endpoints
via TestClient de FastAPI.
"""

from fastapi.testclient import TestClient

from app.config import ajustes
from app.main import app
from app.servicios.predictor import PredictorBKT
from app.servicios.preprocesamiento import cargar_vocab, mapear_concepto

cliente = TestClient(app)


# ------------------------------ Mapeo de conceptos ----------------------------

def test_mapeo_conceptos_conocidos():
    vocab = cargar_vocab(ajustes.ruta_vocab)
    assert mapear_concepto("Derivada del seno", vocab) == "derivada_seno"
    # "coseno" contiene "seno": debe ganar coseno, no seno
    assert mapear_concepto("derivada de coseno", vocab) == "derivada_coseno"
    assert mapear_concepto("Regla de la cadena", vocab) == "regla_cadena"


def test_mapeo_concepto_desconocido():
    vocab = cargar_vocab(ajustes.ruta_vocab)
    assert mapear_concepto("integral por partes", vocab) is None


# --------------------------------- Mastery ------------------------------------

def test_mastery_sube_con_aciertos():
    p = PredictorBKT(ajustes.ruta_modelo)
    m_pocos = p.mastery("derivada_seno", [1])
    m_muchos = p.mastery("derivada_seno", [1, 1, 1, 1])
    assert 0.0 <= m_pocos <= 1.0
    assert m_muchos > m_pocos


# --------------------------------- Endpoints ----------------------------------

def test_health():
    r = cliente.get("/health")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["status"] == "ok"
    assert "derivada_seno" in cuerpo["skills"]


def test_predict_reconoce_y_marca_desconocidos():
    r = cliente.post("/predict", json={"interacciones": [
        {"concepto": "Derivada del seno", "correcto": True},
        {"concepto": "Derivada del seno", "correcto": True},
        {"concepto": "Integral por partes", "correcto": True},
    ]})
    assert r.status_code == 200
    conceptos = r.json()["conceptos"]
    assert conceptos["Derivada del seno"]["reconocido"] is True
    assert conceptos["Derivada del seno"]["nivel"] in (1, 2, 3)
    assert conceptos["Integral por partes"]["reconocido"] is False
