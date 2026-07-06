// Utilidades compartidas para la sección de exámenes.
//
// Contiene helpers reutilizables por tabs de docente y estudiante:
// configuración visual de dificultad, colores de notas y badges,
// colimetría púrpura, configuración de gráficos y cálculo de aciertos.

import { SignalLow, SignalMedium, SignalHigh } from 'lucide-react'
import type { ChartConfig } from '@/components/ui/chart'
import type { Respuesta } from '@/types/analitica'

// Configuración visual de dificultad: label, color e icono.
export const dificultadConfig: Record<
  number,
  { label: string; clase: string; icono: typeof SignalLow }
> = {
  1: {
    label: 'Básico',
    clase:
      'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800',
    icono: SignalLow,
  },
  2: {
    label: 'Intermedio',
    clase:
      'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
    icono: SignalMedium,
  },
  3: {
    label: 'Avanzado',
    clase:
      'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
    icono: SignalHigh,
  },
}

// Devuelve el color de la nota según su valor.
export function colorNota(nota: number): string {
  if (nota >= 4.0) return 'text-emerald-600 dark:text-emerald-400'
  if (nota >= 3.0) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

// Devuelve el color de fondo del badge de aprobados.
export function colorAprobados(porcentaje: number): string {
  if (porcentaje >= 80) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
  if (porcentaje >= 60) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
}

// Configuración de colores para los gráficos (vista individual de intentos).
export const chartConfig = {
  aciertos: { label: 'Aciertos (%)', color: 'var(--chart-2)' },
} satisfies ChartConfig

// Colores de la colimetría púrpura para las barras de cada intento.
export const coloresIntentos = [
  'var(--purple-1)',
  'var(--purple-2)',
  'var(--purple-3)',
  'var(--purple-4)',
  'var(--purple-5)',
]

// Umbral de aprobación.
export const UMBRAL_APROBACION = 3.0

// Calcula aciertos agrupados por un campo (concepto o dificultad).
// Retorna un Map con la clave del campo y el conteo de correctas/total.
export function calcularAciertos(
  respuestas: Respuesta[],
  campo: 'concepto' | 'dificultad'
) {
  const mapa = new Map<
    string | number,
    { correctas: number; total: number }
  >()
  for (const r of respuestas) {
    const clave = r[campo]
    const actual = mapa.get(clave) ?? { correctas: 0, total: 0 }
    mapa.set(clave, {
      correctas: actual.correctas + (r.respuesta_incorrecta ? 0 : 1),
      total: actual.total + 1,
    })
  }
  return mapa
}
