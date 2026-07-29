// Tipos compartidos para los endpoints de /laboratorios/.

export type TipoPregunta = 'codigo' | 'respuesta_libre'

export const OPCIONES_TIPO_PREGUNTA: Array<{ value: TipoPregunta; label: string }> = [
  { value: 'codigo', label: 'Código' },
  { value: 'respuesta_libre', label: 'Respuesta abierta' },
]

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
  tema_estudio: number | null
}

// Caso de test completo (docente): incluye salida esperada y si es público. Solo aplica a tipo=codigo.
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

// Pregunta completa (docente): GET/POST/PATCH en /laboratorios/{id}/preguntas/.
// lenguaje/codigo_inicial/setup_sql/casos_test solo aplican si tipo='codigo'.
// criterios_ia es la rúbrica obligatoria si tipo='respuesta_libre'.
export interface PreguntaDocente {
  id: number
  tipo: TipoPregunta
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
export interface PreguntaPayload {
  tipo: TipoPregunta
  enunciado: string
  lenguaje: LenguajeCodigo
  codigo_inicial: string
  setup_sql: string
  criterios_ia: string
  puntos: number
  orden: number
  casos_test: Array<Omit<CasoTest, 'id'>>
}

// Pregunta para el estudiante: sin criterios_ia, casos_test filtrados a públicos.
export interface PreguntaEstudiante {
  id: number
  tipo: TipoPregunta
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
  tema_estudio: number | null
  preguntas: PreguntaDocente[]
}

// GET /laboratorios/mis-cursos/{curso_id}/laboratorios/{id}/ (estudiante)
export interface LaboratorioDetalleEstudiante {
  id: number
  titulo: string
  instrucciones: string
  max_intentos: number
  fecha_limite: string | null
  creado_en: string
  tema_estudio: number | null
  preguntas: PreguntaEstudiante[]
}

// POST /laboratorios/laboratorios/{id}/preguntas/sugerir-ia/
// Borrador de pregunta (no guardado). Si tipo='codigo', sus casos_test ya
// vienen verificados (la IA propuso una solución de referencia y el backend
// la corrió de verdad en el sandbox). Si tipo='respuesta_libre', no hay
// casos_test ni datos de código.
export interface PreguntaSugerida {
  objetivo_id: number
  objetivo: string
  tipo: TipoPregunta
  enunciado: string
  lenguaje?: LenguajeCodigo
  codigo_inicial?: string
  setup_sql?: string
  criterios_ia: string
  puntos: number
  orden: number
  casos_test: Array<Omit<CasoTest, 'id'>>
}

export interface RespuestaSugerirPreguntas {
  preguntas: PreguntaSugerida[]
  objetivos_sin_generar: string[]
}

// POST /laboratorios/cursos/{cursoId}/laboratorios/sugerir-libre/
// Borrador de pregunta sin objetivo asociado (viene de un enunciado libre, no de la tab Objetivos).
// Este flujo sigue siendo solo de código (el docente elige el lenguaje explícitamente).
export type PreguntaLibreSugerida = Omit<PreguntaSugerida, 'objetivo_id' | 'objetivo'>

export interface RespuestaSugerirLaboratorioLibre {
  titulo: string
  instrucciones: string
  preguntas: PreguntaLibreSugerida[]
}

// POST /laboratorios/preguntas/{id}/ejecutar/ (solo tipo=codigo)
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
  casos_pasados: number | null
  casos_totales: number | null
  puntaje: number
  retroalimentacion: string | null
  intento: number
  intentos_restantes: number | null
  resultados: ResultadoCasoEntrega[]
  enviado_en: string
}

// GET /laboratorios/preguntas/{id}/mis-entregas/
export interface EntregaResumen {
  id: number
  intento: number
  casos_pasados: number | null
  casos_totales: number | null
  puntaje: number
  retroalimentacion: string | null
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
  tipo: TipoPregunta
  lenguaje: LenguajeCodigo | null
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
