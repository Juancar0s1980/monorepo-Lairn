"""
Rutas del microservicio ejecutor. La logica de aislamiento vive en
`app.servicios.sandbox`; aqui solo se valida entrada y se arma la respuesta.
"""

from fastapi import APIRouter

from app.config import ajustes
from app.schemas import (
    PeticionEjecutarCodigo,
    PeticionEjecutarSql,
    RespuestaEjecucion,
    RespuestaHealth,
)
from app.servicios import sandbox

router = APIRouter()


@router.get("/health", response_model=RespuestaHealth, tags=["Salud"])
def health():
    return RespuestaHealth(status="ok", version=ajustes.VERSION, imagenes_listas=sandbox.imagenes_listas())


@router.post("/ejecutar/codigo", response_model=RespuestaEjecucion, tags=["Ejecucion"])
def ejecutar_codigo(peticion: PeticionEjecutarCodigo):
    """Corre codigo del estudiante (Python/JavaScript/Java/C++/C) en un contenedor efimero aislado."""
    resultado = sandbox.ejecutar_codigo(peticion.lenguaje, peticion.codigo, peticion.entrada, peticion.timeout_seg)
    return RespuestaEjecucion(**resultado)


@router.post("/ejecutar/sql", response_model=RespuestaEjecucion, tags=["Ejecucion"])
def ejecutar_sql(peticion: PeticionEjecutarSql):
    """Corre una consulta SQL del estudiante contra SQLite en memoria, en un contenedor efimero aislado."""
    resultado = sandbox.ejecutar_sql(peticion.setup_sql, peticion.consulta, peticion.timeout_seg)
    return RespuestaEjecucion(**resultado)
