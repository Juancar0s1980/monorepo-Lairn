// Tipos compartidos para los endpoints de analítica.
// Usados por los componentes de avance de curso y examen individual.

// Respuesta individual dentro de un resultado de examen.
export interface Respuesta {
  concepto: string
  pregunta: string
  respuesta_correcta: string
  respuesta_incorrecta: string
  tiempo_por_pregunta: number
  dificultad: number
}

// Resultado de un intento de examen.
export interface Resultado {
  id: number
  examen: number
  puntaje: number
  nota: number
  total_preguntas: number
  correctas: number
  completado_en: string
  respuestas: Respuesta[]
}

// GET /analitica/mi-avance/curso/{id}/
export interface AvanceCurso {
  curso_id: number
  curso_nombre: string
  total_examenes_presentados: number
  puntaje_promedio: number
  nota_promedio: number
  resultados: Resultado[]
}

// GET /analitica/mis-resultados/examen/{examen_id}/
export interface ResultadosExamen {
  examen_id: number
  examen_titulo: string
  total_intentos: number
  puntaje_promedio: number
  nota_promedio: number
  resultados: Resultado[]
}

// --- Tipos para endpoint mi-conocimiento ---

// Concepto individual con su nivel de dominio.
export interface ConceptoConocimiento {
  concepto: string
  intentos: number
  correctas: number
  porcentaje_acierto: number
  nivel: number
  nivel_texto: string
}

// Resumen global del conocimiento del estudiante en un curso.
export interface ResumenGlobal {
  concepto_mas_debil: string
  concepto_mas_fuerte: string
  conceptos: ConceptoConocimiento[]
}

// GET /analitica/mi-conocimiento/curso/{curso_id}/
export interface MiConocimiento {
  curso_id: number
  curso_nombre: string
  resumen_global: ResumenGlobal
  por_examen: Array<{
    examen_id: number
    examen_titulo: string
    conceptos: ConceptoConocimiento[]
  }>
}

// --- Tipos para endpoint de patrones del docente ---

// Examen individual dentro de la respuesta de patrones.
export interface ExamenPatron {
  examen_id: number
  titulo: string
  total_presentaciones: number
  nota_promedio: number
  aprobados: number
  porcentaje_aprobados: number
}

// Análisis por nivel de dificultad.
export interface DificultadPatron {
  dificultad: number
  nombre: string
  total_preguntas: number
  correctas: number
  porcentaje_acierto: number
  tiempo_promedio_segundos: number
}

// Concepto con su rendimiento.
export interface ConceptoPatron {
  concepto: string
  total_preguntas: number
  correctas: number
  porcentaje_acierto: number
}

// GET /analitica/curso/{curso_id}/patrones/
export interface PatronesCurso {
  curso: string
  total_inscritos: number
  nota_promedio_curso: number
  examenes: ExamenPatron[]
  analisis_por_dificultad: DificultadPatron[]
  conceptos_mas_debiles: ConceptoPatron[]
  conceptos_mas_fuertes: ConceptoPatron[]
}

// --- Tipos para endpoint de resumen del docente ---

// Estudiante individual dentro del resumen del curso.
export interface EstudianteResumen {
  estudiante_id: number
  nombre: string
  email: string
  examenes_presentados: number
  nota_promedio: number
  aprobados: number
  conceptos_debiles: string[]
}

// GET /analitica/curso/{curso_id}/resumen/
export interface ResumenCursoDocente {
  curso: string
  codigo: string
  total_inscritos: number
  nota_promedio_curso: number
  tasa_aprobacion?: string
  estudiantes: EstudianteResumen[]
}

// --- Tipos para endpoints de administración (Administrador) ---

// GET /analitica/administracion/resumen/
export interface ResumenGlobalAdmin {
  usuarios_por_rol: {
    administrador: number
    docente: number
    estudiante: number
  }
  total_cursos: number
  total_examenes: number
  sesiones_en_progreso: number
  sesiones_completadas: number
  nota_promedio_global: number
  tasa_aprobados_global: number
  cursos_recientes: Array<{ id: number; nombre: string; docente: string; creado_en: string }>
  examenes_recientes: Array<{ id: number; titulo: string; curso: string; creado_en: string }>
  resultados_recientes: Array<{ estudiante: string; examen: string; nota: number; completado_en: string }>
}

// GET /analitica/administracion/cursos/
export interface CursoRendimientoAdmin {
  id: number
  nombre: string
  codigo: string
  docente: string
  total_inscritos: number
  total_examenes: number
  nota_promedio: number
  tasa_aprobados: number
}
