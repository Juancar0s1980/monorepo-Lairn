// Tipos del panel de inicio del Coordinador (ADR-013).
// Coinciden con apps.evaluacion_resultados.services.servicio_panel_coordinador.

import type { Analitica } from '@/types/reporte'

export interface PanelCoordinador {
  programa: number | null
  programas: { id: number; nombre: string }[]
  generado_en: string
  momentos: (Analitica['cobertura'][number] & { publicadas: number; borradores: number })[]
  evaluaciones: Analitica['evaluaciones']
  proximas: {
    id: number
    nombre: string
    tipo: 'cuestionario' | 'tarea'
    momento_id: number
    momento: string
    programa: string
    fecha_inicio: string
    fecha_fin: string
    abierta: boolean
    duracion_minutos: number
    supervisor: string | null
  }[]
  participacion: Analitica['participacion']
  alertas: Analitica['alertas'] & {
    recientes: {
      id: number
      tipo: 'estudiante' | 'curso'
      programa: string
      estudiante: string | null
      asignatura: string | null
      actividades_bajas: number
      total_actividades: number
    }[]
  }
  banco: {
    pendientes: number
    aprobadas: number
    por_asignatura: { asignatura: number; codigo: string; nombre: string; pendientes: number; aprobadas: number }[]
  }
  docentes: {
    docentes: { id: number; nombre: string; email: string; asignaturas: string[]; cursos: number }[]
    asignaturas_sin_curso: number
    asignaturas_con_curso: number
  }
  integridad: Analitica['integridad'] & {
    suspendidos: { estudiante: string; evaluacion: number; nombre: string; momento_id: number; suspendido_en: string; decide: string }[]
  }
}
