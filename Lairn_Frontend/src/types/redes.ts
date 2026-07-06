// Tipos para el panel de Redes Neuronales (solo Administrador).
// Alimentados por:
//   GET /analitica/administracion/redes/modelos/
//   GET /analitica/administracion/redes/resultados/

// --- Estado de las redes (métricas de los modelos) ---

export interface MetricasModelo {
  auc: number | null
  accuracy: number | null
  f1: number | null
  rmse: number | null
}

export interface ModeloRed {
  nombre: string
  tipo: string
  fuente: string
  n_estudiantes: number | null
  n_skills: number | null
  metricas: MetricasModelo
  activo: boolean
}

// GET /analitica/administracion/redes/modelos/
export interface RedesModelos {
  disponible: boolean
  modelo_activo: string | null
  modelos: ModeloRed[]
}

// --- Resultados del Knowledge Tracing ---

export interface DistribucionNiveles {
  debil: number
  desarrollo: number
  dominado: number
}

export interface ResumenNiveles {
  estudiantes: number
  conceptos_evaluados: number
  distribucion_niveles: DistribucionNiveles
  p_dominado_promedio: number | null
  nivel_promedio: number | null
}

export interface ConceptoRed {
  concepto: string
  evaluaciones: number
  nivel_promedio: number | null
  p_dominado_promedio: number | null
}

export interface ProfesorRed extends ResumenNiveles {
  profesor: string
}

// GET /analitica/administracion/redes/resultados/
export interface RedesResultados {
  global: ResumenNiveles
  conceptos: ConceptoRed[]
  por_profesor: ProfesorRed[]
}
