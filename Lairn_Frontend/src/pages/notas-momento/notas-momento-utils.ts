// Utilidades de la página de notas del momento (ADR-019).
import type { ClaveNivel, FilaNotas } from '@/types/notas-momento'

export const CLASE_NIVEL: Record<ClaveNivel, string> = {
  superior: 'border-success/50 text-success',
  alto: 'border-primary/50 text-primary',
  suficiente: 'border-border text-foreground',
  insuficiente: 'border-warning/60 text-warning',
  muy_insuficiente: 'border-destructive/50 text-destructive',
}

export const FILTROS_ESTADO = [
  { clave: 'todos', etiqueta: 'Todos' },
  { clave: 'calificado', etiqueta: 'Con nota del momento' },
  { clave: 'sin_nota', etiqueta: 'Sin nota' },
  { clave: 'no_aprueba', etiqueta: 'No aprueban' },
  { clave: 'ausentes', etiqueta: 'Ausentes o no presentaron' },
  { clave: 'excusa', etiqueta: 'Con excusa' },
  { clave: 'anulado', etiqueta: 'Anulados' },
]

export function coincideFiltro(f: FilaNotas, filtro: string): boolean {
  switch (filtro) {
    case 'calificado':
      return f.momento.nota !== null
    case 'sin_nota':
      return f.momento.nota === null
    case 'no_aprueba':
      return f.momento.aprueba === false
    case 'ausentes':
      return ['ausente', 'no_presento', 'incompleto'].includes(f.examen.estado)
    case 'excusa':
      return f.examen.estado === 'excusa'
    case 'anulado':
      return f.examen.estado === 'anulado'
    default:
      return true
  }
}

// Número con coma decimal (es-CO); "—" si no hay valor.
export function coma(valor: number | null | undefined, decimales = 1): string {
  if (valor === null || valor === undefined) return '—'
  return valor.toLocaleString('es-CO', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}
