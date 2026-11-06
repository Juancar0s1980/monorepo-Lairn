// Helpers compartidos por las vistas de tareas del docente y del estudiante:
// etiquetas, fechas, tiempo restante, nota en vivo y descarga autenticada.

import api from '@/services/api'
import type { CriterioRubrica, EstadoEntrega, FormatoEntrega } from '@/types/tarea'

export const FORMATOS: { valor: FormatoEntrega; etiqueta: string }[] = [
  { valor: 'pdf', etiqueta: 'PDF' },
  { valor: 'documento', etiqueta: 'Word / ODT' },
  { valor: 'zip', etiqueta: 'ZIP' },
  { valor: 'rar', etiqueta: 'RAR' },
  { valor: 'codigo', etiqueta: 'Código fuente' },
  { valor: 'imagen', etiqueta: 'Imagen' },
]

export const ETIQUETA_ENTREGA: Record<EstadoEntrega, { texto: string; clase: string }> = {
  sin_entregar: { texto: 'Sin entregar', clase: 'bg-muted text-muted-foreground' },
  a_tiempo: { texto: 'A tiempo', clase: 'bg-success/10 text-success' },
  con_retraso: { texto: 'Con retraso', clase: 'bg-warning/15 text-foreground' },
}

export const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

// Rúbrica inicial para una tarea manual sin rúbrica en el RA.
export const RUBRICA_INICIAL: CriterioRubrica[] = [
  {
    criterio: 'Cumplimiento del entregable',
    descripcion: '',
    peso: 100,
    niveles: [
      { nombre: 'Bajo', descripcion: '', valor: 1 },
      { nombre: 'Básico', descripcion: '', valor: 3 },
      { nombre: 'Alto', descripcion: '', valor: 5 },
    ],
  },
]

export function tiempoRestante(fechaIso: string, ahora = Date.now()): string {
  const ms = new Date(fechaIso).getTime() - ahora
  if (ms <= 0) return 'Plazo vencido'
  const horas = Math.floor(ms / 3600000)
  if (horas >= 48) return `Quedan ${Math.floor(horas / 24)} días`
  if (horas >= 1) return `Quedan ${horas} h ${Math.floor((ms % 3600000) / 60000)} min`
  return `Quedan ${Math.max(1, Math.floor(ms / 60000))} min`
}

export function tamanoLegible(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

// Misma fórmula que el backend: Σ peso/100 × valor del nivel (escala 0-5).
export function notaPonderada(rubrica: CriterioRubrica[], niveles: (number | null)[]): number | null {
  if (niveles.length !== rubrica.length || niveles.some((n) => n === null)) return null
  const total = rubrica.reduce((suma, c, i) => suma + (c.peso / 100) * c.niveles[niveles[i] as number].valor, 0)
  return Math.round(total * 100) / 100
}

// Los archivos son privados: se piden con el token (Axios) y se guardan como blob.
export async function descargarArchivo(ruta: string, nombre: string) {
  const res = await api.get<Blob>(ruta, { responseType: 'blob', timeout: 60000 })
  const url = URL.createObjectURL(res.data)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}
