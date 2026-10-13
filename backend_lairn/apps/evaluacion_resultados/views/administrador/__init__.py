"""Re-export de vistas de administración."""

from .vista_catalogo import (
    VistaDetalleAsignatura,
    VistaDetalleCompetencia,
    VistaDetalleMomento,
    VistaDetallePrograma,
    VistaDetalleResultado,
    VistaDetalleSemestre,
    VistaDetalleVinculo,
    VistaListaCrearAsignaturas,
    VistaListaCrearCompetencias,
    VistaListaCrearMomentos,
    VistaListaCrearProgramas,
    VistaListaCrearResultados,
    VistaListaCrearSemestres,
    VistaVincularResultadoMomento,
)
from .vista_cargue_documental import (
    VistaAprobarCargue,
    VistaCargarDocumento,
    VistaDetalleCargue,
    VistaListaCargues,
)
from .vista_integracion_nova import VistaImportarJson, VistaListaRegistros, VistaSincronizarNova
from .vista_tablero import VistaTableroPrograma

__all__ = [
    'VistaDetalleAsignatura',
    'VistaDetalleCompetencia',
    'VistaDetalleMomento',
    'VistaDetallePrograma',
    'VistaDetalleResultado',
    'VistaDetalleSemestre',
    'VistaDetalleVinculo',
    'VistaListaCrearAsignaturas',
    'VistaListaCrearCompetencias',
    'VistaListaCrearMomentos',
    'VistaListaCrearProgramas',
    'VistaListaCrearResultados',
    'VistaListaCrearSemestres',
    'VistaVincularResultadoMomento',
    'VistaAprobarCargue',
    'VistaCargarDocumento',
    'VistaDetalleCargue',
    'VistaListaCargues',
    'VistaImportarJson',
    'VistaListaRegistros',
    'VistaSincronizarNova',
    'VistaTableroPrograma',
]
