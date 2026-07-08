// Card de estadística reutilizable.
// Muestra un valor numérico grande con título, icono y subtítulo.
// Usado en dashboard, analítica y tabs de resumen.

import type { LucideIcon } from 'lucide-react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'

interface CardStatProps {
  titulo: string
  valor: string | number
  icono: LucideIcon
  subtitulo?: string
  /** Variante de color del icono. Default: 'accent'. */
  variante?: 'accent' | 'primary' | 'destructivo' | 'exito'
}

// Mapa de clases para las variantes de color.
const variantes = {
  accent: 'bg-accent/15 text-accent',
  primary: 'bg-primary/10 text-primary',
  destructivo: 'bg-destructive/10 text-destructive',
  exito: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
}

export function CardStat({ titulo, valor, icono: Icono, subtitulo, variante = 'accent' }: CardStatProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <p className="text-[11px] font-semibold tracking-[0.08em] uppercase text-muted-foreground">
          {titulo}
        </p>
        <div className={`flex h-8 w-8 items-center justify-center rounded-full ${variantes[variante]}`}>
          <Icono className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tabular-nums">{valor}</div>
        {subtitulo && (
          <p className="text-xs text-muted-foreground mt-1">
            {subtitulo}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
