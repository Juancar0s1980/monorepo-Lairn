// Tipos compartidos para los endpoints de /laboratorios/.

export type LenguajeCodigo = 'python' | 'javascript' | 'java' | 'cpp' | 'c' | 'sql'

export const OPCIONES_LENGUAJE: Array<{ value: LenguajeCodigo; label: string }> = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'c', label: 'C' },
  { value: 'sql', label: 'SQL' },
]

// GET /laboratorios/cursos/{curso_id}/laboratorios/ (colección, ambos roles)
export interface Laboratorio {
  id: number
  titulo: string
  instrucciones: string
  max_intentos: number
  fecha_limite: string | null
  creado_en: string
  total_preguntas: number
}

// Caso de test completo (docente): incluye salida esperada y si es público.
export interface CasoTest {
  id: number
  entrada: string
  salida_esperada: string
  es_publico: boolean
  orden: number
}

// Caso de test público (estudiante): sin el flag es_publico (ya se sabe que lo es).
export interface CasoTestPublico {
  id: number
  entrada: string
  salida_esperada: string
  orden: number
}

// Pregunta de código completa (docente): GET/POST/PATCH en /laboratorios/{id}/preguntas/.
export interface PreguntaCodigoDocente {
  id: number
  enunciado: string
  lenguaje: LenguajeCodigo
  codigo_inicial: string
  setup_sql: string
  criterios_ia: string
  puntos: number
  orden: number
  creado_en: string
  casos_test: CasoTest[]
}

// Payload de creación/edición de una pregunta (sin id/creado_en, casos_test sin id).
export interface PreguntaCodigoPayload {
  enunciado: string
  lenguaje: LenguajeCodigo
  codigo_inicial: string
  setup_sql: string
  criterios_ia: string
  puntos: number
  orden: number
  casos_test: Array<Omit<CasoTest, 'id'>>
}

// Pregunta de código para el estudiante: sin criterios_ia, casos_test filtrados a públicos.
export interface PreguntaCodigoEstudiante {
  id: number
  enunciado: string
  lenguaje: LenguajeCodigo
  codigo_inicial: string
  setup_sql: string
  puntos: number
  orden: number
  casos_test: CasoTestPublico[]
}

// GET /laboratorios/laboratorios/{id}/ (docente)
export interface LaboratorioDetalleDocente {
  id: number
  titulo: string
  instrucciones: string
  max_intentos: number
  fecha_limite: string | null
  creado_en: string
  preguntas: PreguntaCodigoDocente[]
}

// GET /laboratorios/mis-cursos/{curso_id}/laboratorios/{id}/ (estudiante)
export interface LaboratorioDetalleEstudiante {
  id: number
  titulo: string
  instrucciones: string
  max_intentos: number
  fecha_limite: string | null
  creado_en: string
  preguntas: PreguntaCodigoEstudiante[]
}

// POST /laboratorios/laboratorios/{id}/preguntas/sugerir-ia/
// Borrador de pregunta (no guardado): sus casos_test ya vienen verificados
// (la IA propuso una solución de referencia y el backend la corrió de
// verdad en el sandbox para calcular la salida_esperada real).
export interface PreguntaCodigoSugerida {
  objetivo_id: number
  objetivo: string
  enunciado: string
  lenguaje: LenguajeCodigo
  codigo_inicial: string
  setup_sql: string
  criterios_ia: string
  puntos: number
  orden: number
  casos_test: Array<Omit<CasoTest, 'id'>>
}

export interface RespuestaSugerirPreguntasCodigo {
  preguntas: PreguntaCodigoSugerida[]
  objetivos_sin_generar: string[]
}

// POST /laboratorios/cursos/{cursoId}/laboratorios/sugerir-libre/
// Borrador de pregunta sin objetivo asociado (viene de un enunciado libre, no de la tab Objetivos).
export type PreguntaLibreSugerida = Omit<PreguntaCodigoSugerida, 'objetivo_id' | 'objetivo'>

export interface RespuestaSugerirLaboratorioLibre {
  titulo: string
  instrucciones: string
  preguntas: PreguntaLibreSugerida[]
}

// POST /laboratorios/preguntas/{id}/ejecutar/
export interface ResultadoCaso {
  caso_test_id: number
  es_publico: boolean
  paso: boolean
  salida_obtenida: string
  salida_esperada: string
  stderr: string
  timeout: boolean
}

export interface ResultadoEjecucion {
  casos_publicos_totales: number
  casos_publicos_pasados: number
  resultados: ResultadoCaso[]
}

// POST /laboratorios/preguntas/{id}/enviar/
// Igual que ResultadoCaso, pero los casos ocultos vienen con salida_obtenida/
// salida_esperada en null (redactados) — solo se sabe si pasaron o no.
export interface ResultadoCasoEntrega {
  caso_test_id: number
  es_publico: boolean
  paso: boolean
  salida_obtenida: string | null
  salida_esperada: string | null
  stderr: string
  timeout: boolean
}

export interface ResultadoEnvio {
  id: number
  casos_pasados: number
  casos_totales: number
  puntaje: number
  intento: number
  intentos_restantes: number | null
  resultados: ResultadoCasoEntrega[]
  enviado_en: string
}

// GET /laboratorios/preguntas/{id}/mis-entregas/
export interface EntregaResumen {
  id: number
  intento: number
  casos_pasados: number
  casos_totales: number
  puntaje: number
  enviado_en: string
}

export interface MisEntregas {
  entregas: EntregaResumen[]
  max_intentos: number
  intentos_usados: number
  intentos_restantes: number | null
  fecha_limite: string | null
}

// GET /laboratorios/laboratorios/{id}/analitica/
export interface AnaliticaPregunta {
  pregunta_id: number
  enunciado: string
  lenguaje: LenguajeCodigo
  estudiantes_intentaron: number
  estudiantes_resueltas: number
  porcentaje_acierto_promedio: number | null
  intentos_promedio: number | null
}

export interface AnaliticaEstudiante {
  estudiante_id: number
  nombre: string
  email: string
  preguntas_resueltas: number
  total_preguntas: number
  puntaje_promedio: number
}

export interface AnaliticaLaboratorio {
  laboratorio: string
  total_preguntas: number
  total_estudiantes_intentaron: number
  preguntas: AnaliticaPregunta[]
  estudiantes: AnaliticaEstudiante[]
}
