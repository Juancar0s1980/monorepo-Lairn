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
  peso: number
  evidencias: EvidenciaCatalogoSaberPro[]
}

// Competencia del catalogo con sus afirmaciones anidadas.
export interface CompetenciaCatalogoSaberPro {
  id: number
  nombre: string
  peso: number
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
// ---------------------------------------------------------------------------
// Contratos de la HU-19 (creacion y gestion de simulacros). Reflejan
// /docente/cursos/{id}/simulacros/, su disponibilidad de banco aprobado y el
// listado de simulacros activos del estudiante inscrito (HU-19.5).
// ---------------------------------------------------------------------------

export interface DistribucionSimulacro {
  id: number
  competencia: ReferenciaCriterio | null
  afirmacion: ReferenciaCriterio | null
  parte: number | null
  cantidad: number
}

export interface SimulacroSaberPro {
  id: number
  curso: CursoSaberPro
  area: AreaSaberPro
  titulo: string
  descripcion: string
  num_preguntas: number
  tiempo_limite_minutos: number
  intentos_maximos: number
  fecha_limite: string | null
  limite_palabras: number | null
  activo: boolean
  tiene_codigo_desbloqueo: boolean
  total_preguntas: number
  distribuciones: DistribucionSimulacro[]
  creado_en: string
  actualizado_en: string
}

// Pregunta aprobada que quedó asignada al simulacro, con su orden y el
// contenido completo (incluida la respuesta correcta para el docente).
export interface PreguntaAsignadaSimulacro {
  id: number
  orden: number
  contenido: ContenidoBancoSaberPro
}

// Respuesta de GET
// /saber-pro/docente/cursos/{id}/simulacros/{simulacroId}/preguntas/.
export interface PreguntasSimulacroSaberPro {
  simulacro_id: number
  titulo: string
  total_preguntas: number
  preguntas: PreguntaAsignadaSimulacro[]
}

export interface CursoResumenSimulacro {
  id: number
  nombre: string
  area: AreaSaberPro
}

export interface SimulacroEstudianteSaberPro {
  id: number
  curso: CursoResumenSimulacro
  area: AreaSaberPro
  titulo: string
  descripcion: string
  num_preguntas: number
  tiempo_limite_minutos: number
  total_preguntas: number
  intentos_maximos: number
  intentos_realizados: number
  intentos_restantes: number
  intento_en_progreso: boolean
  puede_presentar: boolean
  fecha_limite: string | null
  limite_palabras: number | null
  vencido: boolean
  creado_en: string
}

export interface DatosDistribucionSimulacro {
  competencia_id?: number | null
  afirmacion_id?: number | null
  parte?: number | null
  cantidad?: number | null
}

export interface DatosSimulacroSaberPro {
  titulo?: string
  descripcion?: string
  num_preguntas?: number
  tiempo_limite_minutos?: number
  intentos_maximos?: number
  fecha_limite?: string | null
  limite_palabras?: number | null
  activo?: boolean
  codigo_desbloqueo?: string
  distribuciones?: DatosDistribucionSimulacro[]
}

export interface AfirmacionDisponibilidadSimulacro {
  id: number
  nombre: string
  peso: number
  disponibles: number
}

export interface CompetenciaDisponibilidadSimulacro {
  id: number
  nombre: string
  peso: number
  disponibles: number
  afirmaciones: AfirmacionDisponibilidadSimulacro[]
}

export interface ParteDisponibilidadSimulacro {
  numero: number
  nombre: string
  peso: number
  preguntas: number
  disponibles: number
}

export interface DisponibilidadSimulacroSaberPro {
  area: AreaSaberPro
  tipo_estructura: 'competencias' | 'partes' | 'consigna'
  total_aprobados: number
  competencias: CompetenciaDisponibilidadSimulacro[]
  partes: ParteDisponibilidadSimulacro[]
}

// ---------------------------------------------------------------------------
// Contratos de la HU-21 (presentación cronometrada del simulacro). Las
// respuestas correctas NUNCA llegan al navegador: solo el bloque actual, el
// avance y el resultado final.
// ---------------------------------------------------------------------------

export type SubtipoPreguntaPresentacion =
  | 'opcion_multiple'
  | 'relacionar'
  | 'bloque_ingles'
  | 'consigna'

// Subpregunta de los bloques de Inglés 2 a 7.
export interface PreguntaInternaPresentacion {
  id: number
  enunciado: string
  opciones: string[]
}

export interface PreguntaPresentacionSaberPro {
  id: number
  orden: number
  tipo: 'seleccion_multiple' | 'consigna_escrita'
  subtipo: SubtipoPreguntaPresentacion
  parte: number | null
  tema: string
  contexto: string
  enunciado: string
  opciones: string[]
  descripciones: string[]
  preguntas: PreguntaInternaPresentacion[]
  total_items: number
  limite_palabras: number | null
}

export type MotivoFinalizacionPresentacion =
  | ''
  | 'completada'
  | 'manual'
  | 'tiempo_agotado'
  | 'fecha_limite'

export interface RetroalimentacionRespuestaSaberPro {
  respuesta_id: number
  orden: number
  tema: string
  enunciado: string
  texto: string
  calificacion: number | null
  retroalimentacion: string
  revisada_en: string | null
}

export interface ResultadoPresentacionSaberPro {
  puntaje: number
  calificacion: number
  correctas: number
  total_items: number
  total_evaluables: number
  contenidos_respondidos: number
  total_preguntas: number
  requiere_revision: boolean
  revision_pendiente: boolean
    calificacion_docente: number | null
  retroalimentacion_docente: string
  motivo_finalizacion: MotivoFinalizacionPresentacion
  finalizada_en: string | null
}

export interface ResultadoEstudianteSimulacroSaberPro {
  id: number
  intentos_pendientes: number
  estudiante: {
    id: number
    nombre_completo: string
    email: string
  }
  intento: number
  calificacion: number
  aprobado: boolean
  puntaje: number
  correctas: number
  total_evaluables: number
  contenidos_respondidos: number
  total_preguntas: number
  requiere_revision: boolean
  revision_pendiente: boolean
  motivo_finalizacion: MotivoFinalizacionPresentacion
  iniciada_en: string
  finalizada_en: string | null
}

export interface ResumenResultadosSimulacroSaberPro {
  total_estudiantes: number
  total_intentos: number
  promedio_calificacion: number
  aprobados: number
  requieren_revision: number
}

export interface ResultadosSimulacroSaberPro {
  simulacro_id: number
  simulacro_titulo: string
  intentos_maximos: number
  resumen: ResumenResultadosSimulacroSaberPro
  resultados: ResultadoEstudianteSimulacroSaberPro[]
}

export interface EstadoPresentacionSaberPro {
  presentacion_id: number
  simulacro_id: number
  simulacro_titulo: string
  curso_nombre: string
  area_nombre: string
  intento: number
  estado: 'en_progreso' | 'finalizada'
  bloqueada: boolean
  requiere_codigo_desbloqueo: boolean
  motivo_finalizacion: MotivoFinalizacionPresentacion
  iniciada_en: string
  expira_en: string
  finalizada_en: string | null
  fecha_limite: string | null
  limite_palabras: number | null
  tiempo_limite_minutos: number
  tiempo_restante_segundos: number
  pregunta_numero: number
  total_preguntas: number
  total_items: number
  total_evaluables: number
  contenidos_respondidos: number
  puede_finalizar: boolean
  finalizada: boolean
  pregunta: PreguntaPresentacionSaberPro | null
  resultado: ResultadoPresentacionSaberPro | null
}

export interface RelacionRespuestaPresentacion {
  descripcion: string
  respuesta: string
}

// El cuerpo cambia según el subtipo: solo se envía una de las cuatro formas.
export interface DatosRespuestaPresentacion {
  pregunta_id?: number
  opcion?: string
  relaciones?: RelacionRespuestaPresentacion[]
  respuestas?: string[]
  texto?: string
}

// Contratos de revisión docente de consignas abiertas (HU-24).
// El docente califica el intento completo: una nota y una retroalimentación.
export interface RespuestaRevisionSaberPro {
  id: number
  orden: number
  tema: string
  contexto: string
  enunciado: string
  texto: string
  palabras: number
  limite_palabras: number | null
}

export interface DetalleRevisionSaberPro {
  presentacion_id: number
  simulacro_titulo: string
  estudiante_nombre: string
  intento: number
  puntaje: number
  calificacion: number
  calificacion_docente: number | null
  retroalimentacion: string
  revisada_por: {
    id: number
    nombre_completo: string
  } | null
  revisada_en: string | null
  revision_pendiente: boolean
  total_consignas: number
  respuestas: RespuestaRevisionSaberPro[]
}

export interface DatosRevisionPresentacionSaberPro {
  calificacion: number
  retroalimentacion?: string
}
