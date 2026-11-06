// Tipos de la evaluación formal por momento (HU-06).
// Coinciden con apps.evaluacion_resultados.serializers.serializador_evaluacion_formal.

import type { PreguntaBanco } from '@/types/banco'

export type TipoEvaluacion = 'cuestionario' | 'tarea'
export type EstadoEvaluacion = 'borrador' | 'publicada'

// Por cada RA del momento: cuántas preguntas tiene la evaluación.
export interface CoberturaRA {
  resultado_id: number
  descripcion: string
  obligatorio: boolean
  preguntas: number
}

export interface EvaluacionFormal {
  id: number
  momento: number
  momento_nombre: string
  nombre: string
  instrucciones: string
  tipo: TipoEvaluacion
  // Solo en tipo 'tarea': tarea publicada que se evalúa.
  tarea: number | null
  tarea_titulo: string | null
  fecha_inicio: string
  fecha_fin: string
  duracion_minutos: number
  estado: EstadoEvaluacion
  total_preguntas: number
  cobertura: CoberturaRA[]
  publicada_en: string | null
  creado_en: string
  // ADR-009: docente que hace el llamado a lista (null = sin control de asistencia).
  supervisor: number | null
  supervisor_nombre: string | null
}

// GET /evaluacion/momentos/{id}/banco-elegible/
export interface BancoElegible {
  momento: { id: number; nombre: string; semestre: number }
  excluidas_por_laboratorio: number
  // Tareas publicadas cuyo RA está vinculado al momento (HU-06.4).
  tareas: { id: number; titulo: string; fecha_limite: string; asignatura: string; resultado_id: number }[]
  resultados: {
    resultado: { id: number; descripcion: string; competencia: string }
    obligatorio: boolean
    preguntas: PreguntaBanco[]
  }[]
}
