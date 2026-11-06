// Integridad académica en supervisión y seguimiento (ADR-010).
//
// - `ChipIntegridad`: distintivo del estado (Advertido, Suspendido, …).
// - `PanelIntegridad`: incidentes con hora y tipo, resoluciones previas y, si
//   el intento está suspendido y quien mira puede decidir, los botones
//   Reactivar / Anular por fraude con motivo obligatorio.
// Lo usan el docente supervisor (llamado a lista) y el Coordinador/Admin
// (seguimiento; deciden solo si la evaluación no tiene supervisor).

import { useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Ban, Loader2, PlayCircle, ShieldAlert } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EstadoIntegridad, IntegridadFila } from '@/types/supervision'
import { mensajeError } from '@/pages/academico/academico-utils'
import {
  CLASE_INTEGRIDAD,
  ETIQUETA_CONSECUENCIA,
  ETIQUETA_INCIDENTE,
  ETIQUETA_INTEGRIDAD,
  formatoHoraSegundos,
  reloj,
} from './supervision-utils'

export function ChipIntegridad({ estado }: { estado: EstadoIntegridad | undefined }) {
  if (!estado || estado === 'normal') return null
  return (
    <Badge className={cn('border-transparent', CLASE_INTEGRIDAD[estado])}>
      {estado === 'suspendido' && <ShieldAlert className="mr-1 h-3 w-3" aria-hidden />}
      {ETIQUETA_INTEGRIDAD[estado]}
    </Badge>
  )
}

type Accion = 'reactivar' | 'anular'

export function PanelIntegridad({
  integridad,
  nombre,
  urlResolver,
  puedeResolver,
  motivoNoPuede,
  alResolver,
}: {
  integridad: IntegridadFila
  nombre: string
  urlResolver: string
  puedeResolver: boolean
  motivoNoPuede?: string
  alResolver: () => void
}) {
  const [accion, setAccion] = useState<Accion | null>(null)
  const [motivo, setMotivo] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (integridad.incidentes.length === 0 && integridad.resoluciones.length === 0) return null
  const suspendido = integridad.estado === 'suspendido'
  const lineaDeTiempo = [
    ...integridad.incidentes.map((i, k) => ({
      clave: `i${k}`,
      fecha: i.ocurrido_en,
      decision: false,
      texto: `${ETIQUETA_INCIDENTE[i.tipo]} (${ETIQUETA_CONSECUENCIA[i.consecuencia]})`,
    })),
    ...integridad.resoluciones.map((r, k) => ({
      clave: `r${k}`,
      fecha: r.resuelto_en,
      decision: true,
      texto: `${r.accion === 'reactivar' ? 'Reactivada' : 'Anulada por fraude'}${r.resuelto_por ? ` por ${r.resuelto_por}` : ''}: “${r.motivo}”`,
    })),
  ].sort((a, b) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime())

  const confirmar = async () => {
    if (!accion || !motivo.trim()) return
    setEnviando(true)
    try {
      await api.post(urlResolver, { accion, motivo: motivo.trim() })
      toast.success(accion === 'reactivar' ? `${nombre}: evaluación reactivada` : `${nombre}: evaluación anulada por fraude`)
      setAccion(null)
      setMotivo('')
      alResolver()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo registrar la decisión'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div
      className={cn(
        'space-y-2 rounded-lg border p-3 text-sm',
        suspendido ? 'border-destructive/50 bg-destructive/5' : 'border-border bg-muted/30',
      )}
    >
      <p className="flex flex-wrap items-center gap-2 font-medium text-foreground">
        <ShieldAlert className={cn('h-4 w-4', suspendido ? 'text-destructive' : 'text-warning')} aria-hidden />
        Integridad: {integridad.incidentes_contados} incidente(s) contado(s)
        {suspendido && integridad.segundos_restantes != null && (
          <span className="text-xs font-normal text-muted-foreground">
            · tiempo congelado en {reloj(integridad.segundos_restantes * 1000)}
          </span>
        )}
      </p>
      {/* Línea de tiempo: incidentes y decisiones en orden cronológico. */}
      <ol className="space-y-1 text-xs text-muted-foreground">
        {lineaDeTiempo.map((e) => (
          <li key={e.clave} className={e.decision ? 'text-foreground' : undefined}>
            <span className="font-mono">{formatoHoraSegundos.format(new Date(e.fecha))}</span> · {e.texto}
          </li>
        ))}
      </ol>
      {suspendido &&
        (puedeResolver ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => setAccion('reactivar')}>
              <PlayCircle className="mr-1.5 h-4 w-4" aria-hidden />
              Reactivar
            </Button>
            <Button size="sm" variant="destructive" onClick={() => setAccion('anular')}>
              <Ban className="mr-1.5 h-4 w-4" aria-hidden />
              Anular por fraude
            </Button>
          </div>
        ) : (
          motivoNoPuede && <p className="text-xs text-muted-foreground">{motivoNoPuede}</p>
        ))}

      <Dialog open={accion !== null} onOpenChange={(v) => !v && !enviando && setAccion(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{accion === 'reactivar' ? 'Reactivar evaluación' : 'Anular por fraude'}</DialogTitle>
            <DialogDescription>
              {accion === 'reactivar'
                ? `${nombre} continuará con el tiempo que le quedaba. Un nuevo incidente la suspenderá de inmediato.`
                : `Se cerrará la evaluación de ${nombre} con nota 0 y la marca de fraude. Esta decisión queda registrada y no se puede deshacer.`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="motivo-integridad">
              Motivo <span className="text-destructive" aria-hidden="true">*</span>
            </Label>
            <Textarea
              id="motivo-integridad"
              maxLength={500}
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder={accion === 'reactivar' ? 'Ej.: se le cerró la ventana por una falla del equipo' : 'Ej.: consultó otra pestaña durante la evaluación'}
            />
            <p className="text-right text-xs text-muted-foreground">{motivo.length}/500</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAccion(null)} disabled={enviando}>
              Cancelar
            </Button>
            <Button
              variant={accion === 'anular' ? 'destructive' : 'default'}
              onClick={() => void confirmar()}
              disabled={enviando || !motivo.trim()}
            >
              {enviando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              {accion === 'reactivar' ? 'Reactivar' : 'Anular por fraude'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
