"""
Punto de entrada del servicio FastAPI.

Se arranca con:  uvicorn app.main:app --host 0.0.0.0 --port 8001
"""

from fastapi import FastAPI

from app.api.rutas import router
from app.config import ajustes


def crear_app() -> FastAPI:
    """Fabrica de la aplicacion (patron app factory)."""
    app = FastAPI(
        title=ajustes.NOMBRE,
        version=ajustes.VERSION,
        description="Estima el dominio por concepto con BKT (Bayesian Knowledge Tracing).",
    )
    app.include_router(router)
    return app


app = crear_app()
