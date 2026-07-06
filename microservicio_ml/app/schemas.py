"""
Contratos de datos (Pydantic) de la API: definen y validan lo que entra y sale.

Tenerlos separados del codigo de negocio hace explicito el "contrato" del
servicio y alimenta la documentacion automatica de FastAPI (/docs).
"""

from pydantic import BaseModel, Field


# ------------------------------- Entrada --------------------------------------

class Interaccion(BaseModel):
    """Una respuesta del estudiante a una pregunta."""
    concepto: str = Field(..., description="Concepto en lenguaje natural, ej. 'Derivada del seno'.")
    correcto: bool = Field(..., description="True si el estudiante acerto.")


class PeticionPredict(BaseModel):
    """Cuerpo del POST /predict: interacciones en orden cronologico."""
    interacciones: list[Interaccion] = Field(..., description="Historial ordenado del estudiante.")


# ------------------------------- Salida ---------------------------------------

class ResultadoConcepto(BaseModel):
    """Estimacion de dominio para un concepto."""
    reconocido: bool = Field(..., description="False si el concepto no esta en el vocabulario entrenado.")
    skill: str | None = Field(None, description="Skill entrenado al que se mapeo el concepto.")
    p_dominado: float | None = Field(None, description="P(dominado) segun BKT (0..1).")
    p_acierto_siguiente: float | None = Field(None, description="P(acertar la siguiente pregunta).")
    nivel: int | None = Field(None, description="1=debil, 2=en desarrollo, 3=dominado.")
    n_intentos: int = Field(..., description="Cuantas interacciones se usaron.")


class RespuestaPredict(BaseModel):
    """Respuesta completa del POST /predict."""
    modelo: str
    conceptos: dict[str, ResultadoConcepto]
    dificultad_sugerida: int = Field(..., description="1=Facil, 2=Media, 3=Dificil.")


class RespuestaHealth(BaseModel):
    """Respuesta del GET /health."""
    status: str
    modelo: str
    skills: list[str]
    version: str


# --------------------------- Catalogo de modelos ------------------------------

class MetricasModelo(BaseModel):
    """Metricas de evaluacion de un modelo entrenado."""
    auc: float | None = None
    accuracy: float | None = None
    f1: float | None = None
    rmse: float | None = None


class ModeloInfo(BaseModel):
    """Ficha de un modelo entrenado."""
    nombre: str
    tipo: str
    fuente: str
    n_estudiantes: int | None = None
    n_skills: int | None = None
    metricas: MetricasModelo
    activo: bool = Field(..., description="True si es el modelo que sirve la API.")


class RespuestaModelos(BaseModel):
    """Respuesta del GET /modelos."""
    modelo_activo: str
    modelos: list[ModeloInfo]
