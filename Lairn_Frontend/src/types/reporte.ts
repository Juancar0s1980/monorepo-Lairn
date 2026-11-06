// Tipos del reporte institucional (HU-11) y de la analítica de RA (ADR-011).
// Coinciden con apps.evaluacion_resultados.services.servicio_reporte_ejecutivo
// y servicio_analitica_ra.

export interface Indicadores {
  estudiantes: number
  resultados: number
  promedio: number | null
  desviacion: number | null
  por_encima: number
  por_debajo: number
  distribucion: { rango: string; cantidad: number }[]
}

export interface Integridad {
  suspensiones: number
  anulaciones: number
  reactivaciones: number
  suspendidos_ahora: number
}

// Filtro aplicable al hacer clic (drill-down o celda de un mapa de calor).
export type FiltroReporte = Partial<Record<ClaveFiltro, number | string>>

export const CLAVES_FILTRO = [
  'programa',
  'semestre',
  'momento',
  'desde',
  'hasta',
  'asignatura',
  'docente',
  'competencia',
  'resultado',
  'evaluacion',
] as const
export type ClaveFiltro = (typeof CLAVES_FILTRO)[number]

// Medida de logro (métrica provisional): % de acierto y tamaño de la muestra.
export interface Medida {
  porcentaje: number | null
  aciertos: number
  presentadas: number
  estudiantes: number
  logrado: boolean | null
}

export interface CeldaMapa extends Medida {
  fila: number
  columna: number
  filtro: FiltroReporte
}

export interface MapaCalor {
  filas: { id: number; nombre: string; competencia?: string; tipo?: string }[]
  columnas: { id: number; nombre: string; detalle?: string; codigo?: string }[]
  celdas: CeldaMapa[]
}

export interface LogroRA extends Medida {
  id: number
  descripcion: string
  competencia: string
  tipo: 'especifica' | 'transversal'
  asignatura: string
  programa: string
  filtro: FiltroReporte
}

export interface LogroCompetencia extends Medida {
  id: number
  nombre: string
  tipo: 'especifica' | 'transversal'
  programa: string
  filtro: FiltroReporte
}

export interface Analitica {
  filtros: FiltroReporte
  nivel: 'institucion' | 'programa' | 'semestre' | 'asignatura' | 'resultado' | 'evaluacion'
  ruta: { nivel: string; nombre: string; filtros: FiltroReporte }[]
  fecha_corte: string
  metrica_provisional: { aviso: string; umbral_logro_porcentaje: number; sin_responder_es_fallo: boolean }
  contexto: {
    programas: number
    estudiantes: number
    docentes: number
    coordinadores: number
    asignaturas: number
    cursos: number
    cursos_vinculados: number
  }
  logro_general: Medida & { ra_evaluados: number; ra_logrados: number }
  logro_ra: LogroRA[]
  logro_competencia: LogroCompetencia[]
  logro_por_tipo: Partial<Record<'especifica' | 'transversal', Medida>>
  cobertura: {
    momento: number
    nombre: string
    programa: string
    programa_id: number
    semestre: number
    obligatorios: number
    evaluados: number
    porcentaje: number | null
    sin_evaluar: { id: number; descripcion: string; competencia: string }[]
  }[]
  evaluaciones: { borradores: number; publicadas: number; abiertas: number; presentadas: number; pendientes: number }
  participacion: {
    evaluaciones: number
    convocados: number
    iniciaron: number
    presentaron: number
    anulados: number
    con_control_asistencia: number
    convocados_con_control: number
    presentes: number
    porcentaje_participacion: number | null
    porcentaje_asistencia: number | null
  }
  niveles: {
    niveles: { clave: string; etiqueta: string; minimo: number; cantidad: number; porcentaje: number | null }[]
    total: number
    aprobacion: number | null
  }
  alertas: { abiertas: number; por_tipo: Record<string, number> }
  integridad: Integridad
  mapas: {
    ra_asignatura: MapaCalor
    competencia_programa: MapaCalor
    ra_momento: MapaCalor
    preguntas_error: {
      pregunta: number
      enunciado: string
      asignatura: string
      resultado: string
      presentadas: number
      errores: number
      porcentaje_error: number | null
      filtro: FiltroReporte
    }[]
    participacion_curso: {
      curso: number
      nombre: string
      codigo: string
      convocados: number
      presentaron: number
      porcentaje: number | null
    }[]
  }
  tendencia:
    | { disponible: false; motivo: string; momentos: [] }
    | {
        disponible: true
        momentos: { id: number; nombre: string; programa: string }[]
        general: (Medida & { momento: number })[]
        series: { resultado: number; nombre: string; puntos: ({ momento: number } & Partial<Medida>)[] }[]
      }
  comparacion: {
    por_programa: MedidaComparada[]
    por_semestre: MedidaComparada[]
    por_momento: MedidaComparada[]
    variaciones: { desde: string; hasta: string; antes: number; despues: number; variacion_pp: number }[]
    advertencia: string
  }
  calidad_datos: { clave: string; titulo: string; valor: number; total: number; porcentaje: number | null; impacto: string }[]
  hallazgos: Hallazgo[]
  conclusiones: { puntos: string[]; limitaciones: string[] }
  indicadores_no_disponibles: { nombre: string; referente: string; falta: string }[]
  desglose: {
    nivel: ClaveFiltro | null
    titulo: string
    filas: (Medida & { id: number; nombre: string; filtro: FiltroReporte | null })[]
  }
}

// Ficha técnica de un indicador (ADR-015).
export interface FichaIndicador {
  id: string
  nombre: string
  nivel: 'operativo' | 'estrategico' | 'rendicion'
  provisional: boolean
  tipo: string
  objetivo: string
  definicion: string
  formula: string
  numerador: string
  denominador: string
  unidad: string
  periodicidad: string
  desagregacion: string
  fuente: string
  interpretacion: string
  limitaciones: string
  referente: string
}

export interface Hallazgo {
  tipo: 'atencion' | 'positivo' | 'informativo' | 'calidad'
  prioridad: number
  titulo: string
  detalle: string
  evidencia: { indicador: string; valor: number | null; n: number | null }
  filtro: FiltroReporte | null
  etapa: 'panorama' | 'hallazgos' | 'profundizar' | 'comparar' | 'conclusiones' | 'evidencia'
}

type MedidaComparada = { id: number; nombre: string; porcentaje: number | null; presentadas: number; estudiantes: number; logrado: boolean | null; filtro: FiltroReporte }

export interface Reporte {
  nivel: 'institucion' | 'programa'
  programa?: { id: number; codigo: string; nombre: string }
  indicadores: Indicadores
  integridad: Integridad
  desglose: (Indicadores & { id: number; codigo: string; nombre: string })[]
  analitica: Analitica
}

export interface OpcionesReporte {
  programas: { id: number; nombre: string }[]
  semestres: { id: number; nombre: string }[]
  momentos: { id: number; nombre: string }[]
  asignaturas: { id: number; nombre: string }[]
  docentes: { id: number; nombre: string }[]
  competencias: { id: number; nombre: string }[]
}
