// Card de estadística reutilizable.
// Muestra un valor numérico grande con título, icono y subtítulo.
// Usado en dashboard, analítica y tabs de resumen.

import type { LucideIcon } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

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
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {titulo}
        </CardTitle>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${variantes[variante]}`}>
          <Icono className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-xl font-bold">{valor}</div>
        {subtitulo && (
          <p className="text-xs text-muted-foreground mt-1">
            {subtitulo}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
