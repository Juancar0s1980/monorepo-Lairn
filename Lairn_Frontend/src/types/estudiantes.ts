// Tipos del listado de estudiantes convocados e inscritos (ADR-012).
// Coinciden con apps.evaluacion_resultados.services.servicio_estudiantes.

export type EstadoEstudiante =
  | 'inscrito'
  | 'convocado_curso'
  | 'convocado_cargue'
  | 'presente'
  | 'presento'
  | 'no_presento'
  | 'suspendido'
  | 'anulado'

export interface FilaEstudiante {
  estudiante: number
  nombre: string
  email: string
  codigo: string | null
  programa: string | null
  semestre: number | null
  cursos: string[]
  convocatorias: number
  origenes: ('curso' | 'cargue')[]
  presente: number
  presento: number
  suspendido: number
  anulado: number
  estados: EstadoEstudiante[]
  // Solo si se filtró por una evaluación.
  en_evaluacion?: {
    origen: 'curso' | 'cargue' | null
    presente: boolean
    intento: 'en_curso' | 'enviado' | null
    integridad: string | null
  }
}

export interface ListadoEstudiantes {
  total: number
  pagina: number
  paginas: number
  tamano: number
  conteos: Record<EstadoEstudiante, number>
  estados: Record<EstadoEstudiante, string>
  filas: FilaEstudiante[]
  evaluaciones: { id: number; nombre: string }[]
  evaluacion: { id: number; nombre: string } | null
}
