// Tipos compartidos para exámenes, sesiones y preguntas del motor adaptativo.

// Objetivo de aprendizaje de un curso (los exámenes pueden anclarse a un subconjunto).
export interface ObjetivoCurso {
  id: number
  descripcion: string
  orden: number
  creado_en: string
}

// Modelo de examen tal como lo devuelve el backend.
export interface Examen {
  id: number
  curso: number
  titulo: string
  tema: string
  tiempo: number
  num_preguntas: number
  retroalimentacion: boolean
  dificultad_inicial: number
  max_intentos: number
  fecha_limite: string | null
  es_guiado: boolean
  modo: string
  max_preguntas: number
  // IDs de los objetivos del curso que este examen evalúa (puede venir vacío).
  objetivos?: number[]
  // Porcentaje (0-100) que aporta la práctica (laboratorio vinculado) a la nota final. 0 = solo teoría.
  peso_practica: number
  // Id del laboratorio de práctica vinculado, o null si el examen no tiene práctica.
  laboratorio_practica_id: number | null
  creado_en: string
}

// Respuesta del backend al iniciar o responder en una sesión de examen.
// Los campos de pregunta están al nivel raíz, no dentro de un objeto anidado.
export interface SesionExamen {
  sesion_id: number
  modo: string
  intento_actual: number
  intentos_completados: number
  max_intentos: number
  fecha_limite?: string | null
  dificultad_actual: number
  pregunta: string
  pregunta_numero: number
  opciones: string[]
  explicacion?: string
  total_preguntas: number
  tiempo_total_minutos: number
  // Campos que pueden venir al responder:
  es_correcta?: boolean
  completado?: boolean
  puntaje?: number
  nota?: number
  correctas?: number
  razon_fin?: string
  concepto_evaluado?: string
  // Id del laboratorio de práctica vinculado al examen (solo viene cuando completado=true). Null si no tiene práctica.
  laboratorio_practica_id?: number | null
  // Retroalimentación: null cuando no hay feedback aún, objeto al completar con retroalimentación activada.
  retroalimentacion?: {
    concepto: string
    es_correcta: boolean
    respuesta_correcta: string
  } | null
  // Estado de conceptos evaluados (solo al completar).
  estado_conceptos?: Record<string, { correctas: number; total: number }>
}

// Resultado final cuando el examen se completa.
export interface ResultadoExamen {
  puntaje: number
  nota: number
  correctas: number
  total_preguntas: number
}
