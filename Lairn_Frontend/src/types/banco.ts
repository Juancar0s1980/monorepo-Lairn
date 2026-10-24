// Tipos del banco de preguntas por resultado de aprendizaje (HU-04 / HU-05).
// Coinciden con apps.evaluacion_resultados.serializers.serializador_banco.

export type EstadoPregunta = 'pendiente' | 'aprobada' | 'descartada'

// Asignatura asignada al docente (GET /evaluacion/docente/asignaturas/).
export interface AsignaturaDocente {
  id: number
  codigo: string
  nombre: string
  programa: { id: number; codigo: string; nombre: string }
  curso: { id: number; nombre: string }
  resultados: { id: number; descripcion: string; competencia: { id: number; nombre: string } }[]
  competencias_transversales: { id: number; nombre: string }[]
}

export interface PreguntaBanco {
  id: number
  asignatura: { id: number; codigo: string; nombre: string }
  resultado: {
    id: number
    descripcion: string
    competencia: { id: number; nombre: string; tipo: string }
  }
  competencia_transversal: { id: number; nombre: string } | null
  contexto: string
  enunciado: string
  opciones: string[]
  // Índice (base 0) de la opción correcta.
  respuesta_correcta: number
  retroalimentacion: string
  estado: EstadoPregunta
  origen: 'ia' | 'manual'
  motivo_descarte: string
  revisado_en: string | null
  creado_en: string
  actualizado_en: string
}

// Campos editables durante la curaduría.
export type EdicionPregunta = Pick<
  PreguntaBanco,
  'contexto' | 'enunciado' | 'opciones' | 'respuesta_correcta' | 'retroalimentacion'
>
