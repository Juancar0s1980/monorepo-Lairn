// Tipos del módulo Saber Pro tal como los devuelve `GET /saber-pro/panel/` (HU-16).
//
// HU-16.2: el panel es accesible para Docente y Estudiante sin depender de un
// curso académico. HU-16.3: cuando el usuario aún no tiene cursos Saber Pro
// (`tiene_cursos: false`), el front muestra el estado vacío con la `accion_vacia`
// correspondiente al rol (crear curso para docente, unirse con código para el
// estudiante). Los campos del backend son `snake_case`.

export interface FuncionalidadSaberPro {
  clave: string
  titulo: string
  descripcion: string
  disponible: boolean
}

export type TipoAccionVaciaSaberPro = 'crear_curso' | 'unirse_codigo'

export interface AccionVaciaSaberPro {
  tipo: TipoAccionVaciaSaberPro
  titulo: string
  descripcion: string
  etiqueta_accion: string
}

export interface PanelSaberPro {
  rol: string
  tiene_cursos: boolean
  accion_vacia: AccionVaciaSaberPro | null
  funcionalidades: FuncionalidadSaberPro[]
}

// ---------------------------------------------------------------------------
// Contratos de la HU-17 (creación y gestión de cursos Saber Pro del docente).
// Reflejan las respuestas de /saber-pro/areas/, /saber-pro/docente/cursos/ y
// /saber-pro/docente/cursos/{id}/estudiantes/. Campos del backend en snake_case.
// ---------------------------------------------------------------------------

export interface AreaSaberPro {
  id: number
  nombre: string
}

export interface CursoSaberPro {
  id: number
  nombre: string
  descripcion: string
  area: AreaSaberPro
  codigo: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export interface EstudianteInscrito {
  id: number
  estudiante: {
    id: number
    nombre_completo: string
    email: string
  }
  fecha: string
}

export interface CodigoRegenerado {
  id: number
  codigo: string
  codigo_anterior: string
}

// ---------------------------------------------------------------------------
// Contratos de la HU-18 (inscripción del estudiante por código). Reflejan las
// respuestas de /saber-pro/estudiante/unirse/ y /saber-pro/estudiante/cursos/.
// Una inscripción une al estudiante autenticado con el curso resuelto por el
// código de acceso y conserva la fecha de ingreso (HU-18.3).
// ---------------------------------------------------------------------------

export interface InscripcionCursoSaberPro {
  id: number
  curso: CursoSaberPro
  fecha: string
}

// ---------------------------------------------------------------------------
// Contratos de la HU-20 (banco de contenido generado con IA). Reflejan
// /docente/areas/{id}/criterios/, /docente/cursos/{id}/contenido/ y las
// acciones de generar, editar, aprobar y descartar contenido.
//
// La forma del contenido depende de la estructura del area: seleccion multiple
// con competencia/afirmacion/evidencia (areas estructuradas), seleccion multiple
// con una de las 7 partes de Ingles, o consigna de escritura (Comunicacion
// Escrita). Campos del backend en snake_case.
// ---------------------------------------------------------------------------

// Parte del examen de Ingles (1 a 7): define la tarea, la cantidad de opciones
// y la forma del bloque que se genera. La parte 1 es de relacionar: 8 palabras
// (A-H) para `descripciones` (5). `preguntas` es la cantidad de preguntas del
// bloque completo del examen y `texto_comun` indica si las partes 4 a 7
// comparten un texto base en `contexto`.
export interface ParteInglesSaberPro {
  numero: number
  nombre: string
  peso: number
  opciones: number
  descripciones: number
  preguntas: number
  texto_comun: boolean
  descripcion: string
}

// Evidencia del catalogo anidada dentro de su afirmacion.
export interface EvidenciaCatalogoSaberPro {
  id: number
  nombre: string
}

// Afirmacion del catalogo con sus evidencias (puede no tener ninguna).
export interface AfirmacionCatalogoSaberPro {
  id: number
  nombre: string
  evidencias: EvidenciaCatalogoSaberPro[]
}

// Competencia del catalogo con sus afirmaciones anidadas.
export interface CompetenciaCatalogoSaberPro {
  id: number
  nombre: string
  afirmaciones: AfirmacionCatalogoSaberPro[]
}

// Respuesta de GET /saber-pro/docente/areas/{id}/criterios/ (HU-20.1).
// `tipo_estructura` decide que bloque usar en el formulario de generacion.
export interface CriteriosAreaSaberPro {
  area: AreaSaberPro
  tipo_estructura: 'competencias' | 'partes' | 'consigna'
  competencias: CompetenciaCatalogoSaberPro[]
  partes: ParteInglesSaberPro[]
}

// Referencia minima a un criterio del banco (competencia, afirmacion o evidencia).
export interface ReferenciaCriterio {
  id: number
  nombre: string
}

// Par de la tarea de relacionar (parte 1 de Ingles): une una descripcion con
// una de las 8 palabras del listado A-H. Solo la parte 1 usa `relaciones`.
export interface RelacionContenidoSaberPro {
  descripcion: string
  respuesta: string
}

// Pregunta de una parte 2 a 7 de Ingles: el bloque completo del examen guarda
// todas sus preguntas en `preguntas`; cada una con su enunciado, opciones y
// respuesta. Las partes 4 a 7 comparten un texto base en `contexto` y las 2 y 3
// son preguntas autocontenidas.
export interface PreguntaContenidoSaberPro {
  enunciado: string
  opciones: string[]
  respuesta_correcta: string
}

// Pieza del banco de contenido (pregunta de seleccion multiple o consigna).
// Las referencias a criterios son null cuando el area no las usa; `parte` solo
// aplica a Ingles: cuando es 1, `relaciones` lleva las 5 descripciones, y las
// partes 2 a 7 llevan `preguntas` (el bloque completo del examen).
export interface ContenidoBancoSaberPro {
  id: number
  area: AreaSaberPro
  tipo: 'seleccion_multiple' | 'consigna_escrita'
  estado: 'pendiente' | 'aprobado'
  competencia: ReferenciaCriterio | null
  afirmacion: ReferenciaCriterio | null
  evidencia: ReferenciaCriterio | null
  parte: number | null
  tema: string
  contexto: string
  enunciado: string
  opciones: string[]
  respuesta_correcta: string
  relaciones: RelacionContenidoSaberPro[]
  preguntas: PreguntaContenidoSaberPro[]
  creado_en: string
  actualizado_en: string
  aprobado_en: string | null
}

// Payload de POST /saber-pro/docente/cursos/{id}/contenido/generar/.
// Solo se envia el bloque de criterios que corresponde a la estructura del area.
// En Ingles no se envia `cantidad`: la parte completa se genera como un solo
// bloque y su cantidad de preguntas la define el backend (el examen real).
export interface DatosGenerarContenidoSaberPro {
  competencia_id?: number
  afirmacion_id?: number
  evidencia_id?: number
  parte?: number
  cantidad?: number
}

// Payload de PUT /saber-pro/docente/contenido/{id}/ (edicion de contenido pendiente).
export interface DatosEditarContenidoSaberPro {
  enunciado: string
  opciones?: string[]
  respuesta_correcta?: string
  relaciones?: RelacionContenidoSaberPro[]
  preguntas?: PreguntaContenidoSaberPro[]
  contexto?: string
  tema?: string
}