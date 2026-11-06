// Tipos de supervisión en sala, asistencia, seguimiento en vivo y cargue de
// convocados (ADR-009). Coinciden con
// apps.evaluacion_resultados.services.servicio_supervision.

export type EstadoAsistencia = 'presente' | 'tarde' | 'ausente' | 'excusa'
export type TipoExcusa = 'permiso_medico' | 'calamidad' | 'institucional' | 'otra'

// GET /evaluacion/supervisores-disponibles/
export interface SupervisorDisponible {
  id: number
  nombre: string
  email: string
  total_cursos: number
}

export interface AsistenciaFila {
  estado: EstadoAsistencia
  tipo_excusa: TipoExcusa | null
  observacion: string
  llegada_en: string | null
  actualizado_en: string
}

// Integridad académica del intento (ADR-010).
export type EstadoIntegridad = 'normal' | 'advertido' | 'suspendido' | 'reactivado' | 'anulado_fraude'
export type TipoIncidente =
  | 'copiar'
  | 'cortar'
  | 'pegar'
  | 'menu_contextual'
  | 'cambio_pestana'
  | 'salir_pantalla_completa'
  | 'pantalla_completa_no_disponible'
export type ConsecuenciaIncidente = 'advertencia' | 'suspension' | 'agrupado' | 'sin_efecto'

export interface IntegridadFila {
  estado: EstadoIntegridad
  suspendido_en: string | null
  segundos_restantes: number | null
  incidentes_contados: number
  incidentes: { tipo: TipoIncidente; consecuencia: ConsecuenciaIncidente; ocurrido_en: string; detalle: string }[]
  resoluciones: { accion: 'reactivar' | 'anular'; motivo: string; resuelto_en: string; resuelto_por: string | null }[]
}

export interface IntentoFila {
  integridad: IntegridadFila
  estado: 'en_curso' | 'enviado'
  iniciado_en: string
  vence_en: string
  respondidas: number
  total: number
  enviado_en: string | null
  envio_automatico: boolean
  // Solo para Coordinador/Administrador.
  nota?: string | null
  aciertos?: number | null
}

export interface FilaSeguimiento {
  estudiante: number
  nombre: string
  email: string
  origen: 'curso' | 'cargue'
  asistencia: AsistenciaFila | null
  intento: IntentoFila | null
}

export interface ConteosSeguimiento {
  convocados: number
  presentes: number
  tarde: number
  ausentes: number
  excusa: number
  sin_llamar: number
  en_curso: number
  enviados: number
  sin_iniciar: number
  advertidos: number
  suspendidos: number
  anulados: number
}

export interface ResumenSupervision {
  id: number
  nombre: string
  tipo: 'cuestionario' | 'tarea'
  estado: 'borrador' | 'publicada'
  momento: string
  programa: string
  fecha_inicio: string
  fecha_fin: string
  duracion_minutos: number
  total_preguntas: number
  supervisor: number | null
  supervisor_nombre: string | null
  requiere_asistencia: boolean
  llamado_desde: string
  llamado_hasta: string
}

// GET /evaluacion/evaluaciones/{id}/seguimiento/ y /evaluacion/docente/supervision/{id}/
export interface Seguimiento {
  evaluacion: ResumenSupervision
  ahora_servidor: string
  conteos: ConteosSeguimiento
  filas: FilaSeguimiento[]
}

// GET /evaluacion/docente/supervision/
export interface SupervisionDocente extends ResumenSupervision {
  conteos: ConteosSeguimiento
}

// ADR-012: agregar = válido; no_encontrado = no existe la cuenta; invalido = formato inválido;
// existe = validación global (la cuenta ya existe y es de estudiante).
export type EstadoCargue =
  | 'agregar'
  | 'existe'
  | 'ya_convocado'
  | 'no_encontrado'
  | 'no_es_estudiante'
  | 'duplicado_en_archivo'
  | 'invalido'
  | 'campo_obligatorio_faltante'

// Datos opcionales del archivo y de la cuenta (cuenta + PerfilAcademico). Solo se comparan.
export interface DatosEstudianteArchivo {
  nombre?: string
  codigo?: string
  programa?: string
  semestre?: string
}

// POST /evaluacion/evaluaciones/{id}/convocados/cargue/
export interface InformeCargue {
  filas: {
    fila: number
    correo: string
    estado: EstadoCargue
    estudiante: number | null
    nombre: string | null
    origen: 'curso' | 'cargue' | null
    archivo: DatosEstudianteArchivo
    sistema: {
      nombre: string
      codigo: string | null
      programa: string | null
      semestre: number | null
      tiene_perfil: boolean
    } | null
    diferencias: ('nombre' | 'codigo' | 'programa' | 'semestre')[]
  }[]
  totales: Partial<Record<EstadoCargue, number>>
  total_filas: number
  con_diferencias: number
  columnas: string[]
  confirmado?: boolean
  agregados?: number
}
