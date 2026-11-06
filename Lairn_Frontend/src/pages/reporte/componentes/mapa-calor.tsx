// Mapa de calor del reporte (ADR-011): filas × columnas con el % de logro.
// - Escala de color coherente (`tonoLogro`) y leyenda.
// - Celda sin observaciones = "sin datos" (rayada), nunca 0.
// - Cada celda muestra el valor y el tamaño de la muestra (n) y abre el detalle
//   aplicando su filtro.

import { cn } from '@/lib/utils'
import type { FiltroReporte, MapaCalor as TipoMapa } from '@/types/reporte'
import { pct, tonoLogro } from '../reporte-utils'

export function LeyendaCalor({ umbral }: { umbral: number }) {
  const pasos = [
    { texto: `≥ ${umbral + 20} %`, tono: tonoLogro(umbral + 20, umbral) },
    { texto: `${umbral}–${umbral + 19} %`, tono: tonoLogro(umbral, umbral) },
    { texto: `${umbral - 20}–${umbral - 1} %`, tono: tonoLogro(umbral - 20, umbral) },
    { texto: `< ${umbral - 20} %`, tono: tonoLogro(0, umbral) },
  ]
  return (
    <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground" aria-label="Leyenda de colores">
      {pasos.map((p) => (
        <li key={p.texto} className="flex items-center gap-1.5">
          <span className={cn('h-3 w-3 rounded-sm', p.tono.barra)} aria-hidden />
          {p.texto}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="h-3 w-3 rounded-sm border border-dashed border-muted-foreground/50 bg-muted" aria-hidden />
        Sin datos
      </li>
    </ul>
  )
}

export function MapaCalor({
  mapa,
  umbral,
  etiquetaFilas,
  alAbrir,
}: {
  mapa: TipoMapa
  umbral: number
  etiquetaFilas: string
  alAbrir: (filtro: FiltroReporte) => void
}) {
  if (mapa.celdas.length === 0) {
    return <p className="text-sm text-muted-foreground">Sin datos con los filtros aplicados.</p>
  }
  const celdas = new Map(mapa.celdas.map((c) => [`${c.fila}-${c.columna}`, c]))
  return (
    // Scroll horizontal SOLO dentro del mapa: la página nunca se desborda a 375 px.
    <div className="max-w-full overflow-x-auto rounded-lg border border-border">
      <table className="w-full border-separate border-spacing-1 text-xs">
        <thead>
          <tr>
            <th scope="col" className="sticky left-0 z-10 min-w-40 bg-card p-2 text-left font-medium text-muted-foreground">
              {etiquetaFilas}
            </th>
            {mapa.columnas.map((c) => (
              <th key={c.id} scope="col" className="min-w-24 p-2 text-center font-medium text-muted-foreground" title={c.detalle}>
                {c.nombre}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {mapa.filas.map((f) => (
            <tr key={f.id}>
              <th scope="row" className="sticky left-0 z-10 max-w-56 bg-card p-2 text-left font-normal text-foreground">
                <span className="line-clamp-2">{f.nombre}</span>
                {f.competencia && <span className="block truncate text-[11px] text-muted-foreground">{f.competencia}</span>}
              </th>
              {mapa.columnas.map((c) => {
                const celda = celdas.get(`${f.id}-${c.id}`)
                if (!celda) {
                  return (
                    <td key={c.id} className="rounded-md border border-dashed border-muted-foreground/30 bg-muted/40 p-2 text-center text-muted-foreground">
                      sin datos
                    </td>
                  )
                }
                const tono = tonoLogro(celda.porcentaje, umbral)
                return (
                  <td key={c.id} className="p-0">
                    <button
                      type="button"
                      onClick={() => alAbrir(celda.filtro)}
                      title={`${f.nombre} · ${c.nombre}: ${pct(celda.porcentaje)} (${celda.presentadas} respuestas, ${celda.estudiantes} estudiantes). Clic para ver el detalle.`}
                      className={cn(
                        'w-full rounded-md p-2 text-center transition-colors hover:ring-2 hover:ring-ring/40 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                        tono.fondo,
                      )}
                    >
                      <span className={cn('block text-sm font-semibold tabular-nums', tono.texto)}>{pct(celda.porcentaje)}</span>
                      <span className="block text-[11px] text-muted-foreground">n={celda.presentadas}</span>
                    </button>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
