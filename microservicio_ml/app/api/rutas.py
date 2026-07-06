"""
Rutas (endpoints) de la API. La logica pesada vive en los servicios; aqui solo
se orquesta: validar entrada -> llamar servicios -> construir respuesta.
"""

from fastapi import APIRouter

from app.config import ajustes
from app.schemas import (
    PeticionPredict,
    RespuestaHealth,
    RespuestaModelos,
    RespuestaPredict,
    ResultadoConcepto,
)
from app.servicios.catalogo import listar_modelos
from app.servicios.predictor import PredictorBKT
from app.servicios.preprocesamiento import cargar_vocab, mapear_concepto

# --- Carga unica de artefactos al importar (no en cada request) ---
_predictor = PredictorBKT(ajustes.ruta_modelo)
_vocab = cargar_vocab(ajustes.ruta_vocab)

router = APIRouter()


@router.get("/health", response_model=RespuestaHealth, tags=["Salud"])
def health():
    """Chequeo de salud: usado por el backend y por Docker."""
    return RespuestaHealth(
        status="ok",
        modelo=ajustes.NOMBRE_MODELO,
        skills=_predictor.skills,
        version=ajustes.VERSION,
    )


@router.get("/modelos", response_model=RespuestaModelos, tags=["Catalogo"])
def modelos():
    """Lista todos los modelos entrenados con sus metricas (estado de las redes)."""
    return RespuestaModelos(
        modelo_activo=ajustes.NOMBRE_MODELO,
        modelos=listar_modelos(ajustes.DIR_ARTEFACTOS, ajustes.NOMBRE_MODELO),
    )


@router.post("/predict", response_model=RespuestaPredict, tags=["Prediccion"])
def predict(peticion: PeticionPredict):
    """
    Estima el dominio del estudiante por concepto a partir de sus interacciones.

    Agrupa por concepto, mapea cada uno a un skill entrenado y calcula el mastery
    con BKT. Los conceptos no mapeables se marcan con reconocido=false.
    """
    # 1) Agrupamos las secuencias de aciertos por concepto (preservando orden)
    secuencias: dict[str, list[int]] = {}
    for it in peticion.interacciones:
        secuencias.setdefault(it.concepto, []).append(1 if it.correcto else 0)

    # 2) Mastery/nivel por concepto
    conceptos: dict[str, ResultadoConcepto] = {}
    masteries = []
    for concepto, seq in secuencias.items():
        skill = mapear_concepto(concepto, _vocab)
        if skill is None or skill not in _predictor.skills:
            conceptos[concepto] = ResultadoConcepto(
                reconocido=False, skill=None, p_dominado=None,
                p_acierto_siguiente=None, nivel=None, n_intentos=len(seq),
            )
            continue

        m = _predictor.mastery(skill, seq)
        masteries.append(m)
        conceptos[concepto] = ResultadoConcepto(
            reconocido=True,
            skill=skill,
            p_dominado=round(m, 4),
            p_acierto_siguiente=round(_predictor.p_acierto(skill, m), 4),
            nivel=ajustes.nivel(m),
            n_intentos=len(seq),
        )

    # 3) Dificultad global sugerida por el dominio promedio reconocido
    if masteries:
        dificultad = ajustes.nivel(sum(masteries) / len(masteries))
    else:
        dificultad = 2  # neutral si no hay nada reconocido

    return RespuestaPredict(
        modelo=ajustes.NOMBRE_MODELO,
        conceptos=conceptos,
        dificultad_sugerida=dificultad,
    )
