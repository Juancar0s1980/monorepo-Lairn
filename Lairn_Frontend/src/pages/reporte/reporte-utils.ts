// Utilidades del reporte institucional (ADR-011): escala de color de logro,
// formato de porcentajes y manejo de filtros en la URL.

import { CLAVES_FILTRO, type ClaveFiltro, type FichaIndicador, type FiltroReporte } from '@/types/reporte'

// Recorrido guiado del informe (ADR-015): cada etapa responde una pregunta.
export const ETAPAS = [
  { clave: 'panorama', titulo: 'Panorama', pregunta: '¿Cuál es la situación actual?', ayuda: 'Los indicadores principales con los filtros aplicados. Cada cifra muestra su tamaño de muestra y su ficha técnica.' },
  { clave: 'hallazgos', titulo: 'Hallazgos', pregunta: '¿Qué requiere atención y qué va bien?', ayuda: 'Situaciones relevantes detectadas con reglas explícitas, cada una con su evidencia y un acceso a su detalle.' },
  { clave: 'profundizar', titulo: 'Profundizar', pregunta: '¿Dónde ocurre?', ayuda: 'Baja de la institución al programa, semestre, asignatura, RA y evaluación; cruza RA, competencias, preguntas y cursos.' },
  { clave: 'comparar', titulo: 'Comparar', pregunta: '¿Qué cambió y cómo se comparan?', ayuda: 'Evolución entre momentos y comparación entre programas, semestres y momentos medidos con los mismos criterios.' },
  { clave: 'conclusiones', titulo: 'Conclusiones', pregunta: '¿Qué se puede concluir?', ayuda: 'Síntesis descriptiva de los pasos anteriores, prioridades y limitaciones del análisis.' },
  { clave: 'evidencia', titulo: 'Evidencia y metodología', pregunta: '¿Qué respalda estas cifras?', ayuda: 'Tablas, fichas técnicas, calidad de los datos, indicadores no disponibles y exportación del informe.' },
] as const
export type ClaveEtapa = (typeof ETAPAS)[number]['clave']

export const NIVEL_INDICADOR: Record<FichaIndicador['nivel'], string> = {
  operativo: 'Operativo',
  estrategico: 'Estratégico',
  rendicion: 'Rendición de cuentas',
}

// Escala de color coherente en tarjetas, barras y mapas de calor.
// Se ancla al umbral provisional de logro que envía el servidor (por defecto 60 %).
export interface TonoLogro {
  fondo: string
  texto: string
  barra: string
  etiqueta: string
}

export function tonoLogro(porcentaje: number | null | undefined, umbral = 60): TonoLogro {
  if (porcentaje === null || porcentaje === undefined) {
    return { fondo: 'bg-muted', texto: 'text-muted-foreground', barra: 'bg-muted-foreground/40', etiqueta: 'Sin datos' }
  }
  if (porcentaje >= umbral + 20) return { fondo: 'bg-success/20', texto: 'text-success', barra: 'bg-success', etiqueta: 'Alto' }
  if (porcentaje >= umbral) return { fondo: 'bg-primary/15', texto: 'text-primary', barra: 'bg-primary', etiqueta: 'Logrado' }
  if (porcentaje >= umbral - 20) return { fondo: 'bg-warning/20', texto: 'text-foreground', barra: 'bg-warning', etiqueta: 'En riesgo' }
  return { fondo: 'bg-destructive/15', texto: 'text-destructive', barra: 'bg-destructive', etiqueta: 'Bajo' }
}

export const pct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v.toLocaleString('es-CO')} %`)

// Filtros jerárquicos del drill-down; el resto (momento, fechas, docente, competencia) se conserva al navegar.
export const JERARQUIA: ClaveFiltro[] = ['programa', 'semestre', 'asignatura', 'resultado', 'evaluacion']

export function leerFiltros(params: URLSearchParams): FiltroReporte {
  const filtros: FiltroReporte = {}
  for (const clave of CLAVES_FILTRO) {
    const valor = params.get(clave)
    if (valor) filtros[clave] = valor
  }
  return filtros
}

export function aParams(filtros: FiltroReporte): Record<string, string> {
  const salida: Record<string, string> = {}
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== null && valor !== '') salida[clave] = String(valor)
  }
  return salida
}

// Abre el detalle: aplica el filtro de la celda/fila sobre los filtros actuales.
export function combinar(actuales: FiltroReporte, nuevo: FiltroReporte): FiltroReporte {
  return { ...actuales, ...nuevo }
}

// Ir a un nivel de la ruta: conserva filtros no jerárquicos y reemplaza los jerárquicos.
export function irANivel(actuales: FiltroReporte, filtrosNivel: FiltroReporte): FiltroReporte {
  const base: FiltroReporte = {}
  for (const [clave, valor] of Object.entries(actuales)) {
    if (!JERARQUIA.includes(clave as ClaveFiltro)) base[clave as ClaveFiltro] = valor
  }
  return { ...base, ...filtrosNivel }
}
