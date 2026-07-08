// Encabezado de página reutilizable: eyebrow + título en serif + subtítulo opcional.
// Usado en todas las páginas principales (dashboards, cursos, usuarios, exámenes,
// analítica, moderación, redes) para mantener consistente la jerarquía visual.

import type { ReactNode } from 'react'

interface EncabezadoPaginaProps {
  eyebrow: string
  titulo: ReactNode
  subtitulo?: ReactNode
  /** Slot opcional a la derecha (botón de acción, nota, etc). */
  accion?: ReactNode
}

export function EncabezadoPagina({ eyebrow, titulo, subtitulo, accion }: EncabezadoPaginaProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-primary">
          {eyebrow}
        </p>
        <h1 className="font-heading text-3xl text-balance text-foreground">{titulo}</h1>
        {subtitulo && (
          <div className="mt-2 max-w-prose text-sm text-muted-foreground">{subtitulo}</div>
        )}
      </div>
      {accion}
    </div>
  )
}
