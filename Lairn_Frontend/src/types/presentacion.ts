// Tipos de la presentación de la evaluación formal por el estudiante (HU-07).
// Coinciden con apps.evaluacion_resultados.views.estudiante.vista_evaluaciones_estudiante.

export interface IntentoResumen {
  estado: 'en_curso' | 'enviado'
  iniciado_en: string
  vence_en: string
  enviado_en: string | null
  envio_automatico: boolean
  respondidas: number
  // Integridad académica (ADR-010).
  integridad: 'normal' | 'advertido' | 'suspendido' | 'reactivado' | 'anulado_fraude'
  // Solo si está suspendido: tiempo congelado.
  segundos_restantes: number | null
}

export interface EvaluacionEstudiante {
  id: number
  nombre: string
  instrucciones: string
  tipo: 'cuestionario' | 'tarea'
  momento: string
  fecha_inicio: string
  fecha_fin: string
  duracion_minutos: number
  activa: boolean
  tarea: { id: number; titulo: string } | null
  total_preguntas: number
  intento: IntentoResumen | null
  // ADR-009: con supervisor, solo 'presente' o 'tarde' habilitan iniciar.
  requiere_asistencia: boolean
  asistencia: 'pendiente' | 'presente' | 'tarde' | 'ausente' | 'excusa' | null
}

// Mensaje de espera cuando la asistencia aún no habilita iniciar (o null si puede).
export function bloqueoPorAsistencia(e: EvaluacionEstudiante): string | null {
  if (!e.requiere_asistencia || e.intento) return null
  if (e.asistencia === 'presente' || e.asistencia === 'tarde') return null
  if (e.asistencia === 'ausente') return 'Registrado como ausente'
  if (e.asistencia === 'excusa') return 'Registrado con excusa'
  return 'Esperando llamado a lista'
}

// Pregunta tal como la ve el estudiante: sin respuesta correcta ni justificación.
export interface PreguntaPresentacion {
  id: number
  contexto: string
  enunciado: string
  opciones: string[]
}

export interface DetalleEvaluacionEstudiante extends EvaluacionEstudiante {
  ahora_servidor: string
  // Solo mientras el intento está en curso.
  preguntas?: PreguntaPresentacion[]
  respuestas?: Record<string, number>
}
