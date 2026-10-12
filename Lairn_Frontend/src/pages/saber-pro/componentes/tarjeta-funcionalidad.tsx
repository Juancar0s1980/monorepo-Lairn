// Tarjeta de funcionalidad del módulo Saber Pro (HU-16).
//
// Muestra cada herramienta "que viene" en el panel (HU-19 a HU-24) con la
// identidad visual institucional (.opencode/skills/institutional-ui): chip de
// icono navy, título navy, descripción muted, badge "Próximamente" dorado y
// borde institucional sobre superficie blanca; en oscuro la misma jerarquía
// con los roles invertidos (superficie navy elevada, textos crema, dorado
// aclarado). Una franja gradiente navy→dorado→naranja aparece al pasar el
// cursor y roto para recordar la marca del módulo.
//
// Cuando la funcionalidad todavía no está implementada (`disponible: false`)
// se marca con el badge "Próximamente" y NO es interactiva; cuando una HU
// posterior la habilite, la tarjeta se vuelve clicable a través de `onAccion`.

import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ClipboardList, Sparkles, BarChart3, Trophy, FlaskConical, Target, ArrowUpRight, Lock } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FuncionalidadSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

// Ícono por clave de funcionalidad. Si aparece una clave nueva sin mapear, se usa Sparkles.
const iconoPorClave: Record<string, LucideIcon> = {
  simulacros: ClipboardList,
  banco_contenido: Sparkles,
  analitica: BarChart3,
  ranking: Trophy,
  desempeno: Target,
  laboratorio_practica: FlaskConical,
}

interface TarjetaFuncionalidadProps {
  funcionalidad: FuncionalidadSaberPro
  /** Callback opcional que se dispara al hacer clic en una funcionalidad disponible. */
  onAccion?: () => void
}

export function TarjetaFuncionalidad({ funcionalidad, onAccion }: TarjetaFuncionalidadProps) {
  const Icono = iconoPorClave[funcionalidad.clave] ?? Sparkles
  const interactiva = funcionalidad.disponible && Boolean(onAccion)

  return (
    <Card
      className={cn(
        'group relative h-full transition-all duration-200',
        paletaSaberPro.superficie,
        paletaSaberPro.borde,
        interactiva &&
          'cursor-pointer hover:-translate-y-0.5 hover:border-[#e8740e]/50 hover:shadow-lg dark:hover:border-[#F29A52]/60'
      )}
      onClick={interactiva ? onAccion : undefined}
    >
      {/* Franja gradiente institucional que aparece al pasar el cursor */}
      <div
        aria-hidden="true"
        className={cn(
          'absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#1e3a5f] via-[#c89b14] to-[#e8740e] opacity-0 transition-opacity duration-200',
          'dark:from-[#F3EDE1] dark:via-[#E3C063] dark:to-[#F29A52]',
          interactiva ? 'group-hover:opacity-100' : 'opacity-80'
        )}
      />
      <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
        <span
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-200',
            paletaSaberPro.iconoChip,
            interactiva && 'group-hover:scale-105'
          )}
        >
          <Icono className="h-5 w-5" />
        </span>
        <span className="flex items-center gap-1.5">
          {!funcionalidad.disponible && (
            <>
              <Badge variant="outline" className={cn('gap-1 text-[10px]', paletaSaberPro.badge)}>
                <span className={`h-1.5 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
                Próximamente
              </Badge>
              <Lock className={`h-3 w-3 shrink-0 ${paletaSaberPro.apoyo}`} aria-hidden="true" />
            </>
          )}
          {interactiva && (
            <ArrowUpRight className={`h-4 w-4 ${paletaSaberPro.accion}`} aria-hidden="true" />
          )}
        </span>
      </CardHeader>
      <CardContent>
        <CardTitle className={cn('text-base font-bold', paletaSaberPro.titulo)}>
          {funcionalidad.titulo}
        </CardTitle>
        <p className={cn('mt-1.5 text-xs leading-relaxed', paletaSaberPro.apoyo)}>
          {funcionalidad.descripcion}
        </p>
      </CardContent>
    </Card>
  )
}