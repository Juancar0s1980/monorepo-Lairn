// Aviso de salida durante un simulacro Saber Pro (HU-22.2).
//
// Se muestra cuando el estudiante intenta volver atrás o navegar fuera del
// examen. No se puede cerrar con la X, con Escape ni haciendo clic fuera: solo
// puede continuar en el simulacro o salir enviando el intento. Al salir, el
// intento se finaliza en el backend y no puede reanudarse.

import { LogOut, ShieldAlert, Eye } from 'lucide-react'
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
import { paletaSaberPro } from '../utilidades'

interface Props {
  abierto: boolean
  enviando: boolean
  onContinuar: () => void
  onSalir: () => void
}

export function AvisoProteccionSimulacro({
  abierto,
  enviando,
  onContinuar,
  onSalir,
}: Props) {
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
            <ShieldAlert className="h-6 w-6" />
          </span>
          <DialogTitle className={cn('text-xl', paletaSaberPro.titulo)}>
            ¿Salir del simulacro?
          </DialogTitle>
          <DialogDescription className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>
            Si sales ahora, tus respuestas se enviarán automáticamente y el intento quedará
            finalizado. <strong>No podrás reanudarlo</strong>; si te quedan intentos
            disponibles, podrás iniciar uno nuevo desde tus simulacros.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="gap-2 sm:flex-col">
          <Button
            type="button"
            className={cn('w-full gap-2', paletaSaberPro.botonAccion)}
            onClick={onContinuar}
            disabled={enviando}
          >
            <Eye className="h-4 w-4" />
            Continuar en el simulacro
          </Button>
          <Button
            type="button"
            variant="outline"
            className={cn('w-full gap-2', paletaSaberPro.botonNeutro)}
            onClick={onSalir}
            disabled={enviando}
          >
            <LogOut className="h-4 w-4" />
            {enviando ? 'Enviando intento...' : 'Salir y enviar intento'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
