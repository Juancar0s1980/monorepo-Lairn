// Utilidades de la página de notas del momento (ADR-019).
import type { ClaveNivel, FilaNotas, MomentoConNotas } from '@/types/notas-momento'

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

// --- Filtros del selector de momentos (programa, periodo, fechas y buscador) ---

export interface FiltrosMomento {
  q: string
  programa: string
  periodo: string
  desde: string
  hasta: string
}

const sinTildes = (t: string) => t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()

// Fecha local AAAA-MM-DD (la que ve el usuario), no la UTC del ISO: una evaluación que
// cierra a las 9 p. m. en Colombia ya es "mañana" en UTC.
const formatoISO = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit' })
const diaLocal = (iso: string) => formatoISO.format(new Date(iso))

// Un momento entra si el rango de fechas de sus evaluaciones se cruza con [desde, hasta]
// (mismo criterio que el filtro del backend).
export function filtrarMomentos(momentos: MomentoConNotas[], f: FiltrosMomento): MomentoConNotas[] {
  const q = sinTildes(f.q.trim())
  return momentos.filter((m) => {
    if (f.programa && String(m.programa_id) !== f.programa) return false
    if (f.periodo && m.periodo !== f.periodo) return false
    if (f.desde && (!m.fecha_fin || diaLocal(m.fecha_fin) < f.desde)) return false
    if (f.hasta && (!m.fecha_inicio || diaLocal(m.fecha_inicio) > f.hasta)) return false
    return !q || sinTildes(`${m.nombre} ${m.programa} ${m.periodo}`).includes(q)
  })
}

const formatoDia = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })

export function rangoFechas(m: MomentoConNotas): string {
  if (!m.fecha_inicio || !m.fecha_fin) return ''
  const a = formatoDia.format(new Date(m.fecha_inicio))
  const b = formatoDia.format(new Date(m.fecha_fin))
  return a === b ? a : `${a} – ${b}`
}
