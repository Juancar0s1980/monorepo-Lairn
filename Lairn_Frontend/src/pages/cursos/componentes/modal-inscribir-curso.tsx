// Modal para inscribirse a un curso mediante código.
// Utiliza React Hook Form + Zod para validación del formulario.
// Campo: código (requerido, no vacío).
// Envía POST a /examenes/inscribirse/ y notifica al componente padre.

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, UserPlus, KeyRound } from 'lucide-react'
import { toast } from 'sonner'

// Esquema de validación con Zod.
const esquemaInscribirse = z.object({
  codigo: z.string().min(1, 'El código es obligatorio'),
})

type DatosInscribirse = z.infer<typeof esquemaInscribirse>

// Modelo de respuesta del backend al inscribirse.
// El backend puede responder con `detalle` o `detail` segun la configuracion.
interface RespuestaInscripcion {
  detalle?: string
  detail?: string
}

interface ModalInscribirCursoProps {
  abierta: boolean
  onCerrar: () => void
  onInscripcionExitosa: () => void
}

export function ModalInscribirCurso({
  abierta,
  onCerrar,
  onInscripcionExitosa,
}: ModalInscribirCursoProps) {
  const [enviando, setEnviando] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatosInscribirse>({
    resolver: zodResolver(esquemaInscribirse),
    defaultValues: {
      codigo: '',
    },
  })

  // Envía el código al backend para inscribirse al curso.
  const onSubmit = async (datos: DatosInscribirse) => {
    setEnviando(true)
    try {
      const { data } = await api.post<RespuestaInscripcion>(
        '/examenes/inscribirse/',
        { codigo: datos.codigo }
      )
      const mensaje = data?.detalle ?? data?.detail ?? 'Inscripcion exitosa'
      toast.success(mensaje)
      onInscripcionExitosa()
      reset()
      onCerrar()
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
      }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo inscribir al curso')
      }
    } finally {
      setEnviando(false)
    }
  }

  // Resetea el formulario al cerrar.
  const manejarCerrar = () => {
    reset()
    onCerrar()
  }

  return (
    <Dialog open={abierta} onOpenChange={(open) => !open && manejarCerrar()}>
      <DialogContent className="sm:max-w-lg">
        {/* Header con icono y fondo diferenciado */}
        <DialogHeader className="-mx-4 -mt-4 rounded-t-xl border-b bg-primary/5 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
              <UserPlus className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Inscribirme a un Curso</DialogTitle>
              <DialogDescription>
                Ingresa el código que te dio tu docente
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Campo código */}
          <div className="space-y-1.5">
            <Label htmlFor="codigo">Código de inscripción *</Label>
            <Input
              id="codigo"
              placeholder="Ej: DGXDTBQH"
              maxLength={50}
              {...register('codigo')}
            />
            {errors.codigo && (
              <p className="text-xs text-destructive">
                {errors.codigo.message}
              </p>
            )}
          </div>

          {/* Footer con nota informativa y botones */}
          <DialogFooter>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground sm:mr-auto">
              <KeyRound className="h-3.5 w-3.5" />
              Solicita el código a tu docente
            </p>
            <Button
              type="button"
              variant="outline"
              onClick={manejarCerrar}
              disabled={enviando}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={enviando}>
              {enviando ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Inscribiendo...
                </div>
              ) : (
                'Inscribirme'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
