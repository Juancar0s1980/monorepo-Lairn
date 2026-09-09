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
    clase: 'bg-success/10 text-success border-success/20',
    icono: SignalLow,
  },
  2: {
    label: 'Intermedio',
    clase: 'bg-warning/10 text-warning border-warning/20',
    icono: SignalMedium,
  },
  3: {
    label: 'Avanzado',
    clase: 'bg-destructive/10 text-destructive border-destructive/20',
    icono: SignalHigh,
  },
}

// Devuelve el color de la nota según su valor.
export function colorNota(nota: number): string {
  if (nota >= 4.0) return 'text-success'
  if (nota >= 3.0) return 'text-warning'
  return 'text-destructive'
}

// Devuelve el color de fondo del badge de aprobados.
export function colorAprobados(porcentaje: number): string {
  if (porcentaje >= 80) return 'bg-success/10 text-success'
  if (porcentaje >= 60) return 'bg-warning/10 text-warning'
  return 'bg-destructive/10 text-destructive'
}

// Porcentaje de aprobados, acotado a 100 — aprobados nunca debería superar
// presentados, pero si los datos vienen inconsistentes evita una barra rota.
export function porcentajeAprobados(aprobados: number, presentados: number): number {
  if (presentados <= 0) return 0
  return Math.min(100, Math.round((aprobados / presentados) * 100))
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
