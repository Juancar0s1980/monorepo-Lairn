// Notas del momento (ADR-019).

export type ClaveNivel = 'superior' | 'alto' | 'suficiente' | 'insuficiente' | 'muy_insuficiente'

export interface FilaNotas {
  estudiante_id: number
  codigo: string
  nombre: string
  correo: string
  examen: {
    nota: number | null
    nivel: ClaveNivel | null
    estado: string
    estado_texto: string
    correctas: number | null
    incorrectas: number | null
    sin_responder: number | null
    total: number | null
    porcentaje: number | null
    partes: number
    partes_presentadas: number
    tipo_excusa: string
  }
  trabajo: { nota: number | null; nivel: ClaveNivel | null; estado: string; estado_texto: string; cantidad: number }
  momento: {
    nota: number | null
    nivel: ClaveNivel | null
    aprueba: boolean | null
    estado: 'calificado' | 'pendiente' | 'ponderacion_sin_definir'
    estado_texto: string
    nota_reglamentaria: number | null
    aporte_tercer_corte: number | null
    aporte_definitiva: number | null
  }
}

export interface EsquemaEfectivo {
  peso_momento_en_corte: number | null
  peso_corte_en_definitiva: number | null
  peso_examen: number | null
  peso_trabajo: number | null
  origen_peso_momento_en_corte: string | null
  origen_peso_corte_en_definitiva: string | null
  origen_peso_examen: string | null
  origen_peso_trabajo: string | null
  ponderacion_definida: boolean
}

export interface NotasMomento {
  momento: { id: number; nombre: string; periodo: string; programa: string; semestre_referencia: number }
  generado_en: string
  esquema: EsquemaEfectivo
  evaluaciones: { id: number; nombre: string; tipo: 'cuestionario' | 'tarea'; fecha_fin: string; preguntas: number | null }[]
  tiene_trabajo: boolean
  provisional: boolean
  filas: FilaNotas[]
  resumen: {
    convocados: number
    examen: {
      convocados: number
      presentaron: number
      pct_presentaron: number | null
      ausentes: number
      pct_ausentes: number | null
      con_excusa: number
      anulados: number
      incompletos: number
      en_curso_o_pendientes: number
      promedio: number | null
    }
    trabajo: { promedio: number | null; calificados: number }
    momento: {
      con_nota: number
      promedio: number | null
      niveles: { clave: ClaveNivel; etiqueta: string; cantidad: number; porcentaje: number | null }[]
      aprobados: number
      pct_aprobacion: number | null
      meta_aprobacion: number
      meta_promedio: number
      cumple_aprobacion: boolean | null
      cumple_promedio: boolean | null
    }
    nota_aprobacion: number
    etiquetas_nivel: Record<ClaveNivel, string>
  }
  fuentes: Record<string, string>
  puede_editar_esquema: boolean
}

export interface MomentoConNotas {
  id: number
  nombre: string
  periodo: string
  semestre_referencia: number
  programa_id: number
  programa: string
  // Rango de fechas de sus evaluaciones publicadas (para filtrar por fecha).
  fecha_inicio: string | null
  fecha_fin: string | null
  total_evaluaciones: number
}
