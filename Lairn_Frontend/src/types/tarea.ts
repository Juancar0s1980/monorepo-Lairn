// Tipos de tareas prácticas con rúbrica (HU-08A / HU-08B).
// Coinciden con apps.evaluacion_resultados.serializers.serializador_tarea.

export type FormatoEntrega = 'pdf' | 'documento' | 'zip' | 'rar' | 'codigo' | 'imagen'
export type EstadoPlazo = 'abierta' | 'tardia' | 'cerrada'
export type EstadoEntrega = 'sin_entregar' | 'a_tiempo' | 'con_retraso'

export interface NivelRubrica {
  nombre: string
  descripcion: string
  // Valor en la escala 0-5 que aporta el nivel.
  valor: number
}

export interface CriterioRubrica {
  criterio: string
  descripcion: string
  // Porcentaje; la suma de todos los criterios debe ser 100.
  peso: number
  niveles: NivelRubrica[]
}

export interface ArchivoGuia {
  id: number
  nombre: string
  tamano: number
}

export interface Calificacion {
  nota: string
  niveles_elegidos: number[]
  observaciones: string
  calificada_en: string
}

export interface Entrega {
  id: number
  nombre: string
  tamano: number
  enviada_en: string
  con_retraso: boolean
  estado: EstadoEntrega
  calificacion: Calificacion | null
}

// Vista del docente.
export interface Tarea {
  id: number
  asignatura: { id: number; codigo: string; nombre: string }
  resultado: number
  resultado_descripcion: string
  titulo: string
  descripcion: string
  formatos_permitidos: FormatoEntrega[]
  fecha_limite: string
  permite_tardias: boolean
  rubrica: CriterioRubrica[]
  estado: 'borrador' | 'publicada'
  origen: 'manual' | 'ia'
  archivos_guia: ArchivoGuia[]
  total_entregas: number
  estado_plazo: EstadoPlazo
  publicada_en: string | null
  creado_en: string
}

// Fila del panel de entregas (incluye a quien no ha entregado).
export interface FilaEntrega {
  estudiante: { id: number; email: string; nombre: string }
  entrega: Entrega | null
  estado: EstadoEntrega
}

// Vista del estudiante.
export interface TareaEstudiante {
  id: number
  asignatura: { id: number; codigo: string; nombre: string }
  resultado_descripcion: string
  titulo: string
  descripcion: string
  formatos_permitidos: FormatoEntrega[]
  extensiones: string[]
  fecha_limite: string
  permite_tardias: boolean
  rubrica: CriterioRubrica[]
  archivos_guia: ArchivoGuia[]
  estado_plazo: EstadoPlazo
  mi_entrega: Entrega | null
}
