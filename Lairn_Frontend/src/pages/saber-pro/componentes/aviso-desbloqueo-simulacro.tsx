// Aviso de intento bloqueado durante un simulacro Saber Pro.
//
// Cuando el estudiante cambia de pestaña, sale de pantalla completa o pierde el
// foco, el intento no se cierra: queda bloqueado y se envía una solicitud al
// docente del curso. Este diálogo no se puede cerrar con la X, Escape ni un clic
// fuera; desaparece automáticamente cuando el docente aprueba el desbloqueo. Si
// lo rechaza, el intento se finaliza y se envía automáticamente.

import { Loader2, LockKeyhole, LogOut, RadioTower } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import type { SolicitudDesbloqueoEstudiante } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

const ETIQUETAS_MOTIVO: Record<string, string> = {
  cambio_pestana: 'Detectamos que cambiaste de pestaña',
  pantalla_completa: 'Detectamos que saliste de pantalla completa',
  perdida_foco: 'Detectamos que la ventana del simulacro perdió el foco',
}

interface Props {
  abierto: boolean
  solicitud: SolicitudDesbloqueoEstudiante | null
  enviando: boolean
  onSalir: () => void
}

export function AvisoDesbloqueoSimulacro({
  abierto,
  solicitud,
  enviando,
  onSalir,
}: Props) {
  const motivo = solicitud
    ? ETIQUETAS_MOTIVO[solicitud.motivo] ?? 'Detectamos una salida del simulacro'
    : 'Detectamos una salida del simulacro'

  return (
    <Dialog open={abierto} onOpenChange={() => undefined}>
      <DialogContent
        showCloseButton={false}
        className={cn('max-w-[calc(100%-1.5rem)] sm:max-w-md', paletaSaberPro.superficie)}
      >
        <DialogHeader className="gap-3">
          <span
            className={cn(
              'flex h-12 w-12 items-center justify-center rounded-full',
              paletaSaberPro.chipAccion
            )}
          >
            <LockKeyhole className="h-6 w-6" />
          </span>
          <DialogTitle className={cn('text-xl', paletaSaberPro.titulo)}>
            Simulacro bloqueado
          </DialogTitle>
          <DialogDescription className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>
            {motivo}. Tus respuestas y tu tiempo están guardados. Tu docente recibió una
            notificación y debe desbloquear el intento para que puedas continuar.
          </DialogDescription>
        </DialogHeader>

        <div
          className={cn(
            'flex items-start gap-3 rounded-xl border p-4 text-sm',
            paletaSaberPro.borde,
            paletaSaberPro.bandaAlterna
          )}
        >
          <Loader2 className={cn('mt-0.5 h-5 w-5 shrink-0 animate-spin', paletaSaberPro.accion)} />
          <div>
            <p className={cn('font-semibold', paletaSaberPro.titulo)}>
              Esperando autorización del docente
            </p>
            <p className={cn('mt-1 text-xs leading-relaxed', paletaSaberPro.apoyo)}>
              Esta pantalla se desbloqueará cuando el docente apruebe tu solicitud. Si la
              rechaza, el intento se enviará automáticamente y no podrá reanudarse.
            </p>
          </div>
        </div>

        <div
          className={cn(
            'flex items-start gap-2 rounded-xl border p-3 text-[11px]',
            paletaSaberPro.borde,
            paletaSaberPro.bandaAlterna
          )}
        >
          <RadioTower className={cn('mt-0.5 h-4 w-4 shrink-0', paletaSaberPro.accion)} />
          <p className={paletaSaberPro.texto}>
            Si cierras la pestaña o intentas volver atrás, el intento se enviará y no podrá
            reanudarse.
          </p>
        </div>

        <DialogFooter className="sm:flex-col">
          <Button
            type="button"
            variant="outline"
            className={cn('w-full gap-2', paletaSaberPro.botonNeutro)}
            onClick={onSalir}
            disabled={enviando}
          >
            <LogOut className="h-4 w-4" />
            Cerrar intento y salir
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
