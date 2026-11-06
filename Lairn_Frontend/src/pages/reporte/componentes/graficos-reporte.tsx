// Gráficos del reporte institucional (ADR-011), con recharts vía `components/ui/chart`.
// - TarjetaKpi: indicador con detalle (estilo tablero).
// - BarrasLogro: lista de RA/competencias con barra de % y n (clic = detalle).
// - NivelesDesempeno: distribución por niveles (provisional) con barras.
// - GraficoTendencia: evolución por momentos (solo con ≥ 2 momentos con datos).
// - RadarCompetencias: logro por competencia (≥ 3 competencias).

import { Card, CardContent } from '@/components/ui/card'
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { CartesianGrid, Line, LineChart, PolarAngleAxis, PolarGrid, Radar, RadarChart, ReferenceLine, XAxis, YAxis } from 'recharts'
import { cn } from '@/lib/utils'
import type { Analitica, FiltroReporte, Medida } from '@/types/reporte'
import { pct, tonoLogro } from '../reporte-utils'

const COLORES = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)', 'var(--primary)']

export function TarjetaKpi({
  titulo,
  valor,
  detalle,
  tono,
  accion,
}: {
  titulo: string
  valor: string
  detalle?: string
  tono?: string
  accion?: React.ReactNode
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-1">
          <p className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{titulo}</p>
          {accion}
        </div>
        <p className={cn('mt-1 text-3xl font-semibold tabular-nums', tono ?? 'text-foreground')}>{valor}</p>
        {detalle && <p className="mt-1 text-xs text-muted-foreground">{detalle}</p>}
      </CardContent>
    </Card>
  )
}

export function BarrasLogro({
  filas,
  umbral,
  alAbrir,
}: {
  filas: (Medida & { id: number; titulo: string; subtitulo?: string; etiqueta?: string; filtro?: FiltroReporte | null })[]
  umbral: number
  alAbrir?: (filtro: FiltroReporte) => void
}) {
  if (filas.length === 0) return <p className="text-sm text-muted-foreground">Sin datos con los filtros aplicados.</p>
  return (
    <ul className="space-y-3">
      {filas.map((f) => {
        const tono = tonoLogro(f.porcentaje, umbral)
        const contenido = (
          <>
            <div className="flex items-start justify-between gap-2">
              <span className="min-w-0">
                {f.etiqueta && (
                  <span className="mr-1.5 rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">{f.etiqueta}</span>
                )}
                <span className="text-sm text-foreground">{f.titulo}</span>
                {f.subtitulo && <span className="block text-xs text-muted-foreground">{f.subtitulo}</span>}
              </span>
              <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-medium', tono.fondo, tono.texto)}>{tono.etiqueta}</span>
            </div>
            <div className="mt-1.5 flex items-center gap-2">
              <div className="h-2 flex-1 rounded-full bg-muted" aria-hidden>
                <div className={cn('h-2 rounded-full', tono.barra)} style={{ width: `${Math.min(100, f.porcentaje ?? 0)}%` }} />
              </div>
              <span className="w-14 text-right text-sm font-semibold tabular-nums">{pct(f.porcentaje)}</span>
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              n = {f.presentadas} respuestas · {f.estudiantes} estudiante(s)
            </p>
          </>
        )
        return (
          <li key={f.id}>
            {alAbrir && f.filtro ? (
              <button
                type="button"
                onClick={() => alAbrir(f.filtro!)}
                className="w-full rounded-lg p-1 text-left transition-colors hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                {contenido}
              </button>
            ) : (
              <div className="p-1">{contenido}</div>
            )}
          </li>
        )
      })}
    </ul>
  )
}

const TONO_NIVEL: Record<string, string> = {
  superior: 'bg-success',
  alto: 'bg-chart-4',
  suficiente: 'bg-primary',
  insuficiente: 'bg-warning',
  muy_insuficiente: 'bg-destructive',
}

export function NivelesDesempeno({ niveles }: { niveles: Analitica['niveles'] }) {
  if (niveles.total === 0) return <p className="text-sm text-muted-foreground">Aún no hay notas registradas con estos filtros.</p>
  return (
    <div className="space-y-3">
      <ul className="space-y-2.5">
        {niveles.niveles.map((n) => (
          <li key={n.clave}>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-foreground">
                <span className={cn('h-2.5 w-2.5 rounded-full', TONO_NIVEL[n.clave])} aria-hidden />
                {n.etiqueta} <span className="text-xs text-muted-foreground">(≥ {n.minimo.toFixed(1)})</span>
              </span>
              <span className="font-semibold tabular-nums">
                {pct(n.porcentaje)} <span className="text-xs font-normal text-muted-foreground">({n.cantidad})</span>
              </span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-muted" aria-hidden>
              <div className={cn('h-2 rounded-full', TONO_NIVEL[n.clave])} style={{ width: `${n.porcentaje ?? 0}%` }} />
            </div>
          </li>
        ))}
      </ul>
      <p className="flex justify-between border-t border-border pt-2 text-sm text-muted-foreground">
        Suficiente + Alto + Superior <span className="font-semibold text-success">{pct(niveles.aprobacion)}</span>
      </p>
    </div>
  )
}

export function GraficoTendencia({ tendencia, umbral }: { tendencia: Analitica['tendencia']; umbral: number }) {
  if (!tendencia.disponible) {
    return <p className="text-sm text-muted-foreground">{tendencia.motivo}</p>
  }
  const config: ChartConfig = { general: { label: 'General', color: 'var(--primary)' } }
  tendencia.series.forEach((s, i) => {
    config[`ra${s.resultado}`] = { label: s.nombre.length > 40 ? `${s.nombre.slice(0, 40)}…` : s.nombre, color: COLORES[i % COLORES.length] }
  })
  const datos = tendencia.momentos.map((m, i) => {
    const punto: Record<string, string | number | null> = {
      momento: `${m.nombre} · ${m.programa}`,
      general: tendencia.general[i]?.porcentaje ?? null,
    }
    tendencia.series.forEach((s) => {
      punto[`ra${s.resultado}`] = s.puntos[i]?.porcentaje ?? null
    })
    return punto
  })
  return (
    <ChartContainer config={config} className="h-[300px] w-full">
      <LineChart data={datos} margin={{ left: 0, right: 28, top: 8 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
        {/* Etiquetas cortas: en móvil no se recortan ni se montan. */}
        <XAxis
          dataKey="momento"
          interval={0}
          tickFormatter={(v: string) => (v.length > 14 ? `${v.slice(0, 13)}…` : v)}
          tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
        />
        <YAxis domain={[0, 100]} unit="%" width={44} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} />
        <ReferenceLine y={umbral} stroke="var(--muted-foreground)" strokeDasharray="4 4" label={{ value: `Umbral ${umbral} %`, fontSize: 10, fill: 'var(--muted-foreground)', position: 'insideTopLeft' }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        {tendencia.series.map((s) => (
          <Line key={s.resultado} type="monotone" dataKey={`ra${s.resultado}`} stroke={`var(--color-ra${s.resultado})`} strokeWidth={1.5} strokeDasharray="5 3" dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />
        ))}
        <Line type="monotone" dataKey="general" stroke="var(--color-general)" strokeWidth={3} dot={{ r: 4 }} isAnimationActive={false} />
        <ChartLegend content={<ChartLegendContent />} />
      </LineChart>
    </ChartContainer>
  )
}

export function RadarCompetencias({ competencias }: { competencias: Analitica['logro_competencia'] }) {
  const config: ChartConfig = { porcentaje: { label: '% de logro', color: 'var(--primary)' } }
  const datos = competencias.map((c) => ({ competencia: c.nombre.length > 22 ? `${c.nombre.slice(0, 22)}…` : c.nombre, porcentaje: c.porcentaje ?? 0 }))
  return (
    <ChartContainer config={config} className="mx-auto h-[260px] w-full max-w-md">
      <RadarChart data={datos} outerRadius="70%">
        <PolarGrid stroke="var(--border)" />
        <PolarAngleAxis dataKey="competencia" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Radar dataKey="porcentaje" stroke="var(--color-porcentaje)" fill="var(--color-porcentaje)" fillOpacity={0.3} />
      </RadarChart>
    </ChartContainer>
  )
}
