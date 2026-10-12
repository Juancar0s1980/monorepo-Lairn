// Modal para que el estudiante se una a un curso Saber Pro con el código de
// acceso (HU-18.1, validación HU-18.2 y rechazo de duplicado HU-18.4).
//
// El estudiante ingresa el código de 8 caracteres que le compartió su docente y
// el backend resuelve la inscripción (POST /saber-pro/estudiante/unirse/). El
// capital, la validación de formato y los mensajes de error de dominio los
// maneja el backend; aquí solo se normaliza a mayúsculas en el input y se
// aplanan los errores de validación en un toast (patrón estándar del front).
// Al inscribirse, se notifica al padre con la inscripción creada para que
// refresque el panel (HU-18.3).

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, KeyRound, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import type { InscripcionCursoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

// Esquema de validación de Zod: el código es obligatorio y de 8 caracteres.
const esquemaUnirseCursoSaberPro = z.object({
  codigo: z
    .string()
    .min(1, 'El código es obligatorio')
    .max(8, 'El código de acceso tiene 8 caracteres'),
})

type DatosUnirseCursoSaberPro = z.infer<typeof esquemaUnirseCursoSaberPro>

interface ModalUnirseCursoSaberProProps {
  abierta: boolean
  onCerrar: () => void
  onInscripcionExitosa: (inscripcion: InscripcionCursoSaberPro) => void
}

export function ModalUnirseCursoSaberPro({
  abierta,
  onCerrar,
  onInscripcionExitosa,
}: ModalUnirseCursoSaberProProps) {
  const [enviando, setEnviando] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatosUnirseCursoSaberPro>({
    resolver: zodResolver(esquemaUnirseCursoSaberPro),
    defaultValues: { codigo: '' },
  })

  // Separamos el registro del campo para combinar el onChange de RHF con la
  // normalización a mayúsculas (los códigos los genera el sistema en mayúsculas, HU-17.2).
  const { ref: refCodigo, onChange: onChangeCodigo, ...restoCodigo } = register('codigo')

  // Envía el código al backend; el sistema resuelve la inscripción (HU-18).
  const onSubmit = async (datos: DatosUnirseCursoSaberPro) => {
    setEnviando(true)
    try {
      const { data } = await api.post<InscripcionCursoSaberPro>('/saber-pro/estudiante/unirse/', {
        codigo: datos.codigo,
      })
      toast.success(`Te uniste a "${data.curso.nombre}"`)
      reset()
      onInscripcionExitosa(data)
      onCerrar()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo unir al curso Saber Pro')
    } finally {
      setEnviando(false)
    }
  }

  // Al cerrar se limpia el formulario para la próxima apertura.
  const manejarCerrar = () => {
    reset()
    onCerrar()
  }

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && manejarCerrar()}>
      <DialogContent className="max-h-[85vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-md">
        {/*
          Encabezado sobre la superficie clara: chip de acción + título
          institucional, misma estructura que los demás modales del módulo.
        */}
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}
            >
              <KeyRound className="h-6 w-6" />
            </span>
            <div className="flex items-center gap-2">
              <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
                Inscripción por código
              </p>
            </div>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>
              Unirme a un curso Saber Pro
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Ingresa el código de acceso que te compartió tu docente para unirte
              a su curso de preparación.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className={`space-y-4 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
        >
          {/* Código de acceso del curso (se normaliza a mayúsculas al escribir) */}
          <div className="space-y-1.5">
            <Label htmlFor="codigo" className={`${paletaSaberPro.titulo}`}>
              Código de acceso *
            </Label>
            <Input
              id="codigo"
              placeholder="Ej: DGXDTBQH"
              maxLength={8}
              autoFocus
              spellCheck={false}
              className={`bg-white uppercase tracking-[0.2em] dark:bg-[#243A5E] ${paletaSaberPro.titulo}`}
              ref={refCodigo}
              {...restoCodigo}
              onChange={(e) => {
                e.target.value = e.target.value.toUpperCase()
                void onChangeCodigo(e)
              }}
            />
            {errors.codigo && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.codigo.message}</p>
            )}
          </div>

          {/* Pie: nota de confianza + botones */}
          <div className={`border-t pt-4 ${paletaSaberPro.borde}`}>
            <p className={`flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
              <ShieldCheck className={`h-3.5 w-3.5 ${paletaSaberPro.accion}`} />
              El código es único por curso y te lo comparte tu docente (HU-18).
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <Button
                type="button"
                className={`${paletaSaberPro.botonNeutro}`}
                onClick={manejarCerrar}
                disabled={enviando}
              >
                Cancelar
              </Button>
              <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={enviando}>
                {enviando ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Uniéndome...
                  </>
                ) : (
                  <>
                    <KeyRound className="h-4 w-4" />
                    Unirme al curso
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}