// Asignación masiva de docentes a asignaturas (ADR-017).

export type EstadoAsignacion = 'valida' | 'advertencia' | 'ya_asignada' | 'omitida' | 'error'

export interface FilaAsignacion {
  fila: number
  asignatura_codigo: string
  docente_email: string
  curso_codigo: string
  asignatura: { id: number; codigo: string; nombre: string; programa: string } | null
  docente: { email: string; nombre: string } | null
  curso: { codigo: string | null; nombre: string } | null
  anterior: { curso: string; codigo: string; docente_email: string; docente: string } | null
  crear_curso: boolean
  estado: EstadoAsignacion
  mensaje: string
  aplicada?: boolean
}

export interface ResumenAsignacion {
  valida: number
  advertencia: number
  ya_asignada: number
  omitida: number
  error: number
  total: number
  cursos_nuevos: number
  cambios_docente: number
  asignadas?: number
  cursos_creados?: number
}

export interface AnalisisAsignacion {
  programa: { id: number; codigo: string; nombre: string }
  resumen: ResumenAsignacion
  filas: FilaAsignacion[]
  entrada: Record<string, unknown>[]
  huella: string
}

export interface ResultadoAsignacion {
  registro_id: number
  programa: { id: number; codigo: string; nombre: string }
  resumen: ResumenAsignacion
  filas: FilaAsignacion[]
}
