"""
Paquete de modelos de la app `evaluacion_resultados`.

Re-exporta todo para importar corto:
  from apps.evaluacion_resultados.models import ProgramaAcademico
"""

from .modelo_banco import OpcionesEstadoPregunta, OpcionesOrigenPregunta, PreguntaBanco
from .modelo_base import ModeloTrazable, OpcionesEstadoRevision, OpcionesOrigen
from .modelo_evaluacion_formal import (
    EvaluacionFormal,
    EvaluacionPregunta,
    OpcionesEstadoEvaluacion,
    OpcionesTipoEvaluacion,
)
from .modelo_tarea import (
    ArchivoGuiaTarea,
    EntregaTarea,
    OpcionesEstadoTarea,
    TareaPractica,
)
from .modelo_intento import IntentoEvaluacion, OpcionesIntegridad
from .modelo_integridad import (
    TIPOS_INFORMATIVOS,
    IncidenteIntento,
    OpcionesAccionIntegridad,
    OpcionesConsecuencia,
    OpcionesTipoIncidente,
    ResolucionIntegridad,
)
from .modelo_supervision import (
    ESTADOS_HABILITAN,
    AsistenciaEvaluacion,
    ConvocadoEvaluacion,
    OpcionesEstadoAsistencia,
    OpcionesTipoExcusa,
)
from .modelo_alerta import AlertaDesempeno, OpcionesEstadoAlerta, OpcionesTipoAlerta, ReglaAlerta
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

from .modelo_ayuda import ArticuloAyuda, OpcionesCategoriaAyuda
from .modelo_esquema import EsquemaCalificacion

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
    'PreguntaBanco',
    'OpcionesEstadoPregunta',
    'OpcionesOrigenPregunta',
    'EvaluacionFormal',
    'EvaluacionPregunta',
    'OpcionesEstadoEvaluacion',
    'OpcionesTipoEvaluacion',
    'TareaPractica',
    'ArchivoGuiaTarea',
    'EntregaTarea',
    'OpcionesEstadoTarea',
    'IntentoEvaluacion',
    'OpcionesIntegridad',
    'IncidenteIntento',
    'ResolucionIntegridad',
    'OpcionesTipoIncidente',
    'OpcionesConsecuencia',
    'OpcionesAccionIntegridad',
    'TIPOS_INFORMATIVOS',
    'ConvocadoEvaluacion',
    'AsistenciaEvaluacion',
    'OpcionesEstadoAsistencia',
    'OpcionesTipoExcusa',
    'ESTADOS_HABILITAN',
    'ReglaAlerta',
    'AlertaDesempeno',
    'OpcionesEstadoAlerta',
    'OpcionesTipoAlerta',
    'ArticuloAyuda',
    'OpcionesCategoriaAyuda',
    'EsquemaCalificacion',
]
