"""
Contratos de datos (Pydantic) del microservicio ejecutor.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


class PeticionEjecutarCodigo(BaseModel):
    """Cuerpo del POST /ejecutar/codigo. Cubre todos los lenguajes menos SQL."""
    lenguaje: Literal["python", "javascript", "java", "cpp", "c"] = Field(..., description="Lenguaje del codigo.")
    codigo: str = Field(..., description="Codigo enviado por el estudiante.")
    entrada: str = Field("", description="Texto que recibira el codigo por stdin.")
    timeout_seg: float | None = Field(None, description="Limite de tiempo; se recorta al maximo permitido.")


class PeticionEjecutarSql(BaseModel):
    """Cuerpo del POST /ejecutar/sql."""
    setup_sql: str = Field("", description="DDL/DML para crear y poblar las tablas antes de la consulta.")
    consulta: str = Field(..., description="Consulta SQL enviada por el estudiante.")
    timeout_seg: float | None = Field(None, description="Limite de tiempo; se recorta al maximo permitido.")


class RespuestaEjecucion(BaseModel):
    """Respuesta comun a ambos endpoints de ejecucion."""
    lenguaje: Literal["python", "javascript", "java", "cpp", "c", "sql"]
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    filas: list[list[Any]] | None = None
    columnas: list[str] | None = None
    error: str | None = None
    timeout: bool = False
    tiempo_ms: int
    compilado: bool | None = None
    error_compilacion: str | None = None


class RespuestaHealth(BaseModel):
    status: str
    version: str
    imagenes_listas: dict[str, bool]
