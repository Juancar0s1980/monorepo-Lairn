"""
Punto de entrada del microservicio ejecutor.

Se arranca con:  uvicorn app.main:app --host 0.0.0.0 --port 8003

Al arrancar, construye las imagenes "runner" (python/sql) si no existen
todavia en el daemon de Docker, para que la primera ejecucion de un
estudiante no pague ese costo (y para fallar rapido en el arranque si el
socket de Docker no esta disponible, en vez de fallar silenciosamente en
la primera peticion real).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.rutas import router
from app.config import ajustes
from app.servicios import sandbox


@asynccontextmanager
async def lifespan(app: FastAPI):
    sandbox.asegurar_imagenes()
    yield


def crear_app() -> FastAPI:
    app = FastAPI(
        title=ajustes.NOMBRE,
        version=ajustes.VERSION,
        description="Ejecuta codigo de estudiantes (Python, SQL) de forma aislada en contenedores efimeros.",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = crear_app()
