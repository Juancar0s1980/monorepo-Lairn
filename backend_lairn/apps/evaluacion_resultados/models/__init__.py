"""
Paquete de modelos de la app `evaluacion_resultados`.

Re-exporta todo para importar corto:
  from apps.evaluacion_resultados.models import ProgramaAcademico
"""

from .modelo_base import ModeloTrazable, OpcionesEstadoRevision, OpcionesOrigen
from .modelo_dce import Competencia, OpcionesTipoCompetencia, ResultadoAprendizaje
from .modelo_malla import AsignaturaMalla, OpcionesTipoAsignatura, SemestrePrograma
from .modelo_momento import MomentoEvaluacion, MomentoResultado
from .modelo_programa import ProgramaAcademico
from .modelo_trazabilidad import (
    CargueDocumental,
    OpcionesEstadoCargue,
    OpcionesEstadoUsuario,
    OpcionesTipoDocumento,
    PerfilAcademico,
    RegistroSincronizacion,
)

__all__ = [
    'ModeloTrazable',
    'OpcionesOrigen',
    'OpcionesEstadoRevision',
    'ProgramaAcademico',
    'SemestrePrograma',
    'AsignaturaMalla',
    'OpcionesTipoAsignatura',
    'Competencia',
    'ResultadoAprendizaje',
    'OpcionesTipoCompetencia',
    'MomentoEvaluacion',
    'MomentoResultado',
    'PerfilAcademico',
    'OpcionesEstadoUsuario',
    'CargueDocumental',
    'OpcionesTipoDocumento',
    'OpcionesEstadoCargue',
    'RegistroSincronizacion',
]
