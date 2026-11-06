"""Re-export de vistas de administración."""

from .vista_asignacion_docentes import VistaAnalizarAsignacion, VistaConfirmarAsignacion, VistaPlantillaAsignacion
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
from .vista_integracion_nova import (
    VistaImportarJson,
    VistaImportarUrl,
    VistaListaRegistros,
    VistaSincronizarNova,
)
from .vista_tablero import VistaTableroPrograma
from .vista_cursos_vinculables import VistaCursosVinculables
from .vista_desempeno_ra import VistaDesempenoRA
from .vista_reporte_ejecutivo import (
    VistaCatalogoIndicadores,
    VistaExportarReporte,
    VistaOpcionesReporte,
    VistaReporteEjecutivo,
)
from .vista_alertas import VistaAlertasPrograma, VistaAtenderAlerta, VistaExportarAlertas, VistaReglaAlerta
from .vista_panel_coordinador import VistaPanelCoordinador
from .vista_paneles_rol import VistaPanelAdmin, VistaPanelDocente, VistaPanelEstudiante
from .vista_estudiantes import VistaEstudiantesDocente, VistaEstudiantesGestor, VistaValidarEstudiantes
from .vista_supervision import (
    VistaAsignarSupervisor,
    VistaCargueConvocados,
    VistaQuitarConvocado,
    VistaResolverIntegridadGestor,
    VistaSeguimientoEvaluacion,
    VistaSupervisoresDisponibles,
)
from .vista_evaluacion_formal import (
    VistaBancoElegible,
    VistaDetalleEvaluacion,
    VistaListaCrearEvaluaciones,
    VistaPublicarEvaluacion,
    VistaSeleccionPreguntas,
)

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
    'VistaImportarUrl',
    'VistaListaRegistros',
    'VistaSincronizarNova',
    'VistaTableroPrograma',
    'VistaCursosVinculables',
    'VistaDesempenoRA',
    'VistaExportarReporte',
    'VistaReporteEjecutivo',
    'VistaOpcionesReporte',
    'VistaCatalogoIndicadores',
    'VistaAlertasPrograma',
    'VistaAtenderAlerta',
    'VistaExportarAlertas',
    'VistaReglaAlerta',
    'VistaBancoElegible',
    'VistaDetalleEvaluacion',
    'VistaListaCrearEvaluaciones',
    'VistaPublicarEvaluacion',
    'VistaSeleccionPreguntas',
    'VistaEstudiantesDocente',
    'VistaPanelCoordinador',
    'VistaPanelAdmin',
    'VistaPanelDocente',
    'VistaPanelEstudiante',
    'VistaEstudiantesGestor',
    'VistaValidarEstudiantes',
    'VistaAsignarSupervisor',
    'VistaCargueConvocados',
    'VistaQuitarConvocado',
    'VistaResolverIntegridadGestor',
    'VistaSeguimientoEvaluacion',
    'VistaSupervisoresDisponibles',
    'VistaAnalizarAsignacion',
    'VistaConfirmarAsignacion',
    'VistaPlantillaAsignacion',
]
