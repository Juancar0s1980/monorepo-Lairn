// Piezas del recorrido guiado del reporte (ADR-015).
// - EtapasNav: navegación por las 6 etapas (panorama → evidencia), accesible
//   como lista de pasos con la etapa actual marcada.
// - Seccion: tarjeta con título, pregunta que responde, periodo/unidad y fuente.
// - BotonFicha + DialogoFicha: ficha técnica del indicador (fórmula, fuente,
//   limitaciones) a un clic desde cada cifra.
// - TarjetaHallazgo: situación relevante con su evidencia y acceso al detalle.

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { AlertTriangle, CheckCircle2, Database, Info, Lightbulb, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FichaIndicador, Hallazgo } from '@/types/reporte'
import { ETAPAS, NIVEL_INDICADOR, type ClaveEtapa } from '../reporte-utils'

export function EtapasNav({ actual, alElegir }: { actual: ClaveEtapa; alElegir: (e: ClaveEtapa) => void }) {
  return (
    <nav aria-label="Etapas del análisis" className="sticky top-0 z-20 -mx-1 overflow-x-auto bg-background/95 px-1 py-2 backdrop-blur">
      <ol className="flex min-w-max gap-1.5">
        {ETAPAS.map((e, i) => {
          const activa = e.clave === actual
          return (
            <li key={e.clave}>
              <button
                type="button"
                onClick={() => alElegir(e.clave)}
                aria-current={activa ? 'step' : undefined}
                className={cn(
                  'flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                  activa ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground hover:bg-muted',
                )}
              >
                <span className={cn('flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold', activa ? 'bg-primary-foreground/20' : 'bg-muted')}>
                  {i + 1}
                </span>
                {e.titulo}
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export function Seccion({
  titulo,
  descripcion,
  fuente,
  accion,
  children,
}: {
  titulo: string
  descripcion?: string
  fuente?: string
  accion?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <Card className="min-w-0">
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
        <div className="min-w-0">
          <CardTitle className="text-base">{titulo}</CardTitle>
          {descripcion && <CardDescription>{descripcion}</CardDescription>}
        </div>
        {accion}
      </CardHeader>
      <CardContent className="min-w-0 space-y-3">
        {children}
        {fuente && <p className="border-t border-border pt-2 text-[11px] text-muted-foreground">Fuente: {fuente}</p>}
      </CardContent>
    </Card>
  )
}

export function BotonFicha({ ficha, alAbrir }: { ficha: FichaIndicador | undefined; alAbrir: (f: FichaIndicador) => void }) {
  if (!ficha) return null
  return (
    <button
      type="button"
      onClick={() => alAbrir(ficha)}
      aria-label={`Ficha técnica: ${ficha.nombre}`}
      title="Ver ficha técnica (cómo se calcula)"
      className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
    >
      <Info className="h-4 w-4" aria-hidden />
    </button>
  )
}

const FILAS_FICHA: [keyof FichaIndicador, string][] = [
  ['objetivo', 'Objetivo'],
  ['definicion', 'Definición'],
  ['formula', 'Fórmula'],
  ['numerador', 'Numerador'],
  ['denominador', 'Denominador'],
  ['unidad', 'Unidad'],
  ['periodicidad', 'Periodicidad'],
  ['desagregacion', 'Desagregación'],
  ['fuente', 'Fuente'],
  ['interpretacion', 'Interpretación'],
  ['limitaciones', 'Limitaciones'],
  ['referente', 'Referente'],
]

export function DialogoFicha({ ficha, alCerrar }: { ficha: FichaIndicador | null; alCerrar: () => void }) {
  return (
    <Dialog open={!!ficha} onOpenChange={(v) => !v && alCerrar()}>
      <DialogContent className="sm:max-w-2xl">
        {ficha && (
          <>
            <DialogHeader>
              <DialogTitle>{ficha.nombre}</DialogTitle>
              <DialogDescription className="flex flex-wrap gap-1.5">
                <Badge variant="outline" className="font-normal">{ficha.tipo}</Badge>
                <Badge variant="outline" className="font-normal">Nivel: {NIVEL_INDICADOR[ficha.nivel]}</Badge>
                {ficha.provisional && <Badge variant="outline" className="border-warning/60 font-normal">Métrica provisional</Badge>}
              </DialogDescription>
            </DialogHeader>
            <dl className="grid gap-x-4 gap-y-2 text-sm sm:grid-cols-[9rem_1fr]">
              {FILAS_FICHA.map(([clave, etiqueta]) => (
                <div key={clave} className="contents">
                  <dt className="font-medium text-muted-foreground">{etiqueta}</dt>
                  <dd className="text-foreground">{String(ficha[clave])}</dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

const ESTILO_HALLAZGO: Record<Hallazgo['tipo'], { icono: typeof Info; clase: string; etiqueta: string }> = {
  atencion: { icono: AlertTriangle, clase: 'border-warning/50 bg-warning/5', etiqueta: 'Requiere atención' },
  positivo: { icono: CheckCircle2, clase: 'border-success/40 bg-success/5', etiqueta: 'Resultado favorable' },
  informativo: { icono: Lightbulb, clase: 'border-primary/40 bg-primary/5', etiqueta: 'Para tener en cuenta' },
  calidad: { icono: Database, clase: 'border-border bg-muted/40', etiqueta: 'Calidad de los datos' },
}

export function TarjetaHallazgo({ hallazgo, alAbrir }: { hallazgo: Hallazgo; alAbrir?: () => void }) {
  const estilo = ESTILO_HALLAZGO[hallazgo.tipo]
  const ev = hallazgo.evidencia
  return (
    <li className={cn('space-y-2 rounded-xl border p-4', estilo.clase)}>
      <div className="flex items-start gap-2">
        <estilo.icono className="mt-0.5 h-4 w-4 shrink-0 text-foreground" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{estilo.etiqueta}</p>
          <p className="font-medium text-foreground">{hallazgo.titulo}</p>
          <p className="text-sm text-muted-foreground">{hallazgo.detalle}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 pl-6">
        <span className="text-xs text-muted-foreground">
          Evidencia: {ev.indicador.replaceAll('_', ' ')}
          {ev.valor !== null && ` = ${ev.valor}`}
          {ev.n !== null && ev.n !== undefined && ` · n = ${ev.n}`}
        </span>
        {alAbrir && (
          <Button variant="outline" size="sm" onClick={alAbrir}>
            <Search className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Ver detalle
          </Button>
        )}
      </div>
    </li>
  )
}
