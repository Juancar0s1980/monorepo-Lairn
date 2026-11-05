// Aviso de permanencia obligatoria durante un simulacro Saber Pro (HU-22.2).
//
// El diálogo no se puede cerrar con la X, con Escape ni haciendo clic fuera.
// Si el docente configuró un código, el intento queda bloqueado en el backend y
// el estudiante solo puede reanudarlo ingresando ese código. Si el simulacro es
// antiguo y no tiene código, se mantiene la advertencia visual con el botón de
// volver para no dejar al estudiante atrapado sin salida.

import { AlertCircle, Eye, KeyRound, LockKeyhole, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

interface Props {
  abierto: boolean
  requiereCodigo: boolean
  codigo: string
  onCodigoChange: (valor: string) => void
  onDesbloquear: () => void
  onVolver: () => void
  desbloqueando: boolean
  error: string | null
}

export function AvisoProteccionSimulacro({
  abierto,
  requiereCodigo,
  codigo,
  onCodigoChange,
  onDesbloquear,
  onVolver,
  desbloqueando,
  error,
}: Props) {
  const puedeDesbloquear = Boolean(codigo.trim()) && !desbloqueando

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
            {requiereCodigo ? 'Examen bloqueado' : 'Mantente en el simulacro'}
          </DialogTitle>
          <DialogDescription className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>
            {requiereCodigo
              ? 'Detectamos que saliste de la pantalla del simulacro. El intento quedó bloqueado y el cronómetro sigue corriendo. Ingresa el código que te entregó tu docente para reanudarlo.'
              : 'Detectamos que saliste de la pantalla del simulacro. Para continuar, vuelve a esta ventana y confirma que estás listo para retomar.'}
          </DialogDescription>
        </DialogHeader>

        {requiereCodigo ? (
          <form
            className="space-y-3"
            onSubmit={(evento) => {
              evento.preventDefault()
              if (puedeDesbloquear) onDesbloquear()
            }}
          >
            <div className="space-y-1.5">
              <Label htmlFor="codigo-desbloqueo" className={paletaSaberPro.titulo}>
                <KeyRound className="mr-1 inline h-3.5 w-3.5" />
                Código de desbloqueo
              </Label>
              <Input
                id="codigo-desbloqueo"
                value={codigo}
                onChange={(evento) => onCodigoChange(evento.target.value.toUpperCase())}
                maxLength={32}
                autoComplete="off"
                autoFocus
                disabled={desbloqueando}
                placeholder="Ingresa el código del docente"
                className="bg-white font-mono tracking-[0.18em] dark:bg-[#243A5E]"
              />
            </div>

            {error && (
              <p className="flex items-start gap-1.5 text-xs text-[#b8432a] dark:text-[#F29A52]">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {error}
              </p>
            )}

            <DialogFooter className="gap-2">
              <Button
                type="submit"
                disabled={!puedeDesbloquear}
                className={cn('w-full gap-2', paletaSaberPro.botonAccion)}
              >
                <LockKeyhole className="h-4 w-4" />
                {desbloqueando ? 'Validando código...' : 'Desbloquear examen'}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <DialogFooter className="gap-2">
            <Button
              type="button"
              className={cn('w-full gap-2', paletaSaberPro.botonAccion)}
              onClick={onVolver}
            >
              <Eye className="h-4 w-4" />
              Volver al simulacro
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
