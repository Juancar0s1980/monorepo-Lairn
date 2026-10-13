// Modelos TypeScript del módulo de Evaluación de Resultados
// (Módulo 1 - Configuración e Información Académica).
// Coinciden con los serializers de apps.evaluacion_resultados.

// Origen de un registro: manual, documento + IA, API NOVA o semilla.
export type Origen = 'manual' | 'documento_ia' | 'api_nova' | 'semilla'

// Estado de revisión para curaduría de propuestas IA.
export type EstadoRevision =
  | 'borrador_ia'
  | 'pendiente'
  | 'aprobado'
  | 'descartado'
  | 'inactivo'

// Programa académico (HU-01.1 / 01.2 / 01.3).
export interface ProgramaAcademico {
  id: number
  codigo: string
  nombre: string
  modalidad: string
  sede: string
  duracion_semestres: number
  fecha_vigencia: string | null
  estado: string
  origen: Origen
  external_id: string | null
  estado_revision: EstadoRevision
  version: number
  activo: boolean
  total_semestres: number
  creado_en: string
}

// Semestre dentro de un programa (HU-01.4).
export interface SemestrePrograma {
  id: number
  numero: number
  nombre: string
  origen: Origen
  estado_revision: EstadoRevision
  activo: boolean
  creado_en: string
}

// Asignatura de la malla curricular (HU-01.5).
export interface AsignaturaMalla {
  id: number
  codigo: string
  nombre: string
  creditos: number
  intensidad_horaria: number
  tipo: 'obligatoria' | 'electiva' | 'optativa' | 'practica'
  semestre: number | null
  // Número legible del semestre (lo envía el backend para no hacer join).
  semestre_numero?: number | null
  curso_vinculado: number | null
  origen: Origen
  external_id: string | null
  estado_revision: EstadoRevision
  activo: boolean
  creado_en: string
}

// Competencia transversal o específica (HU-01.6).
export interface Competencia {
  id: number
  nombre: string
  tipo: 'transversal' | 'especifica'
  descripcion: string
  origen: Origen
  estado_revision: EstadoRevision
  activo: boolean
  creado_en: string
}

// Resultado de aprendizaje con estructura DCE (HU-01.7 / 01.8).
export interface ResultadoAprendizaje {
  id: number
  competencia: number
  asignatura: number
  descripcion: string
  evidencia_observable: string
  tarea_sugerida: string
  criterios_rubrica: CriterioRubrica[]
  version: number
  activo: boolean
  estado_revision: EstadoRevision
  origen: Origen
  creado_en: string
}

// Criterio de rúbrica estructurada: los pesos suman 100.
export interface CriterioRubrica {
  criterio: string
  niveles: string
  peso: number
}

// Momento de evaluación por programa/semestre (HU-02.1).
export interface MomentoEvaluacion {
  id: number
  semestre_referencia: number
  nombre: string
  periodo: string
  descripcion: string
  origen: Origen
  estado_revision: EstadoRevision
  activo: boolean
  total_ras: number
  creado_en: string
}

// Vínculo Momento -> RA (HU-02.2).
export interface MomentoResultado {
  id: number
  resultado: number
  // Descripción legible del RA (la envía el backend).
  resultado_descripcion?: string
  obligatorio: boolean
  creado_en: string
}

// Tablero resumido de un programa (HU-02.3).
export interface TableroPrograma {
  programa: { id: number; codigo: string; nombre: string }
  totales: {
    semestres: number
    asignaturas: number
    competencias: number
    momentos: number
  }
  momentos: {
    momento_id: number
    nombre: string
    semestre: number
    total_ras: number
    ras: { id: number; descripcion: string; obligatorio: boolean }[]
  }[]
}

// Cargue documental procesado con IA.
export interface CargueDocumental {
  id: number
  tipo: 'pensum' | 'resolucion' | 'plan_aula'
  nombre_archivo: string
  programa: number | null
  // Nombre del programa destino (lo envía el backend para la revisión).
  programa_nombre?: string | null
  estado: 'procesado' | 'aprobado' | 'rechazado' | 'fallido'
  propuesta_json: Record<string, unknown>
  // Causa del fallo (solo cuando estado === 'fallido').
  detalle_error?: string
  creado_en: string
}

// Respuesta del aprobar-cargue: qué se incorporó al programa.
export interface ResultadoAprobacionCargue {
  cargue_id: number
  programa_id: number
  incorporados: number
  detalle: {
    asignaturas: number
    momentos: number
    competencias: number
    resultados: number
  }
  errores: string[]
}

// Corrección de una fila de la propuesta antes de incorporar.
export interface CorreccionPropuesta {
  indice: number
  codigo?: string
  nombre?: string
  creditos?: number
  intensidad?: number
  tipo?: string
  semestre?: number
}

// Resumen de una importación JSON NOVA (HU-03).
export interface ResumenImportacion {
  registro_id: number
  modo: 'simulacro' | 'real'
  total_recibidos: number
  creados: number
  actualizados: number
  omitidos: number
  errores: string[]
}
