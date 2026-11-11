// Solicitudes de vinculación curso ↔ asignatura de la malla (HU-01.10).
// Coinciden con apps.evaluacion_resultados.views.vista_vinculacion.

export type EstadoSolicitud = 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada'

export interface CursoVinculado {
  id: number
  nombre: string
  docente: string
  docente_email: string
}

export interface AsignaturaVinculable {
  id: number
  codigo: string
  nombre: string
  semestre: number | null
  programa: { id: number; codigo: string; nombre: string }
  curso_vinculado: CursoVinculado | null
}

export interface ProgramaVinculable {
  id: number
  codigo: string
  nombre: string
  asignaturas: AsignaturaVinculable[]
}

export interface SolicitudVinculacion {
  id: number
  estado: EstadoSolicitud
  mensaje: string
  respuesta: string
  creada_en: string
  resuelta_en: string | null
  resuelta_por: string
  reemplazo_curso: string
  curso: { id: number; nombre: string; codigo: string }
  docente: { id: number; nombre: string; email: string }
  asignatura: AsignaturaVinculable
}

export interface VinculacionCurso {
  curso: { id: number; nombre: string; codigo: string }
  vinculadas: AsignaturaVinculable[]
  solicitudes: SolicitudVinculacion[]
}
