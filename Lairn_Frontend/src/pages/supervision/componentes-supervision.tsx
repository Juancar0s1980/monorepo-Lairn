// Componentes visuales compartidos de supervisión en sala (ADR-009): chip de
// asistencia, progreso del intento y tarjetas de conteo.

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ConteosSeguimiento, EstadoAsistencia, IntentoFila } from '@/types/supervision'
import { CLASE_ASISTENCIA, ETIQUETA_ASISTENCIA, reloj } from './supervision-utils'

export function ChipAsistencia({ estado }: { estado: EstadoAsistencia | null | undefined }) {
  if (!estado) return <Badge className="border-transparent bg-muted text-muted-foreground">Sin llamar</Badge>
  return <Badge className={cn('border-transparent', CLASE_ASISTENCIA[estado])}>{ETIQUETA_ASISTENCIA[estado]}</Badge>
}

// Progreso del intento: sin iniciar / en curso con tiempo restante / enviado.
export function ProgresoIntento({ intento, ahoraServidor }: { intento: IntentoFila | null; ahoraServidor: number }) {
  if (!intento) return <span className="text-xs text-muted-foreground">Sin iniciar</span>
  const suspendido = intento.integridad?.estado === 'suspendido'
  const anulado = intento.integridad?.estado === 'anulado_fraude'
  const barra = intento.total ? Math.round((intento.respondidas / intento.total) * 100) : 0
  return (
    <div className="min-w-[8rem] space-y-1">
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className={anulado || suspendido ? 'text-destructive' : intento.estado === 'enviado' ? 'text-success' : 'text-foreground'}>
          {anulado
            ? 'Anulada (fraude)'
            : suspendido
              ? 'Suspendida'
              : intento.estado === 'enviado'
                ? intento.envio_automatico
                  ? 'Enviada (tiempo)'
                  : 'Enviada'
                : 'En curso'}
        </span>
        <span className="text-muted-foreground">
          {intento.respondidas}/{intento.total}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-muted" aria-hidden>
        <div
          className={cn('h-1.5 rounded-full', anulado || suspendido ? 'bg-destructive' : intento.estado === 'enviado' ? 'bg-success' : 'bg-primary')}
          style={{ width: `${barra}%` }}
        />
      </div>
      {intento.estado === 'en_curso' && !suspendido && (
        <p className="font-mono text-xs text-muted-foreground">
          Quedan {reloj(new Date(intento.vence_en).getTime() - ahoraServidor)}
        </p>
      )}
      {suspendido && intento.integridad.segundos_restantes != null && (
        <p className="font-mono text-xs text-destructive">Congelado en {reloj(intento.integridad.segundos_restantes * 1000)}</p>
      )}
    </div>
  )
}

const TARJETAS: { clave: keyof ConteosSeguimiento; titulo: string; clase?: string }[] = [
  { clave: 'convocados', titulo: 'Convocados' },
  { clave: 'presentes', titulo: 'Presentes', clase: 'text-success' },
  { clave: 'tarde', titulo: 'Tarde' },
  { clave: 'ausentes', titulo: 'Ausentes', clase: 'text-destructive' },
  { clave: 'excusa', titulo: 'Excusa', clase: 'text-primary' },
  { clave: 'sin_llamar', titulo: 'Sin llamar' },
  { clave: 'en_curso', titulo: 'En curso', clase: 'text-primary' },
  { clave: 'enviados', titulo: 'Enviados', clase: 'text-success' },
  { clave: 'suspendidos', titulo: 'Suspendidos', clase: 'text-destructive' },
  { clave: 'anulados', titulo: 'Anulados (fraude)', clase: 'text-destructive' },
]

export function TarjetasConteo({ conteos }: { conteos: ConteosSeguimiento }) {
  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {TARJETAS.map((t) => (
        <div key={t.clave} className="rounded-xl border border-border bg-card p-3">
          <dt className="text-xs text-muted-foreground">{t.titulo}</dt>
          <dd className={cn('text-2xl font-semibold text-foreground', t.clase)}>{conteos[t.clave]}</dd>
        </div>
      ))}
    </dl>
  )
}
