// Modal para crear un curso Saber Pro del docente (HU-17.1 y HU-17.2).
//
// El docente elige el área del catálogo oficial (servido por /saber-pro/areas/),
// define el nombre y, opcionalmente, la descripción. El código de acceso NO lo
// escribe el docente: el backend lo genera automáticamente y único (HU-17.2).
// Al crear, POST /saber-pro/docente/cursos/ y se notifica al padre con el curso
// devuelto (incluye el código autogenerado) para refrescar la lista.

import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, BookMarked, Hash, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import type { AreaSaberPro, CursoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerLargo } from '../utilidades'

// Esquema de validación de Zod: área obligatoria, nombre obligatorio (<= 100).
const esquemaCrearCursoSaberPro = z.object({
  area_id: z.string().min(1, 'Selecciona el área de Saber Pro'),
  nombre: z.string().min(1, 'El nombre es obligatorio').max(100, 'Máximo 100 caracteres'),
  descripcion: z.string().max(500, 'Máximo 500 caracteres').optional(),
})

type DatosCrearCursoSaberPro = z.infer<typeof esquemaCrearCursoSaberPro>

interface ModalCrearCursoSaberProProps {
  abierta: boolean
  onCerrar: () => void
  onCursoCreado: (curso: CursoSaberPro) => void
}

export function ModalCrearCursoSaberPro({
  abierta,
  onCerrar,
  onCursoCreado,
}: ModalCrearCursoSaberProProps) {
  const [enviando, setEnviando] = useState(false)
  const [areas, setAreas] = useState<AreaSaberPro[]>([])

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<DatosCrearCursoSaberPro>({
    resolver: zodResolver(esquemaCrearCursoSaberPro),
    defaultValues: {
      area_id: '',
      nombre: '',
      descripcion: '',
    },
  })

  // Carga el catálogo de áreas Saber Pro al abrir el modal.
  useEffect(() => {
    if (!abierta) return
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<AreaSaberPro[]>('/saber-pro/areas/', {
          signal: controlador.signal,
        })
        setAreas(data)
      } catch {
        // Sin áreas disponibles el selector simplemente queda vacío.
      }
    }
    cargar()
    return () => controlador.abort()
  }, [abierta])

  // Envía la creación al backend; el código lo genera el propio servidor (HU-17.2).
  const onSubmit = async (datos: DatosCrearCursoSaberPro) => {
    setEnviando(true)
    try {
      const { data } = await api.post<CursoSaberPro>('/saber-pro/docente/cursos/', {
        area_id: Number(datos.area_id),
        nombre: datos.nombre,
        descripcion: datos.descripcion || '',
      })
      toast.success('Curso Saber Pro creado')
      reset()
      onCursoCreado(data)
      onCerrar()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo crear el curso Saber Pro')
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
          Encabezado sobre la superficie clara. Replica la estructura de los
          modales institucionales del módulo: chip de accion + título.
        */}
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}
            >
              <BookMarked className="h-6 w-6" />
            </span>
            <div className="flex items-center gap-2">
              <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
                Curso de preparación
              </p>
            </div>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>
              Crear curso Saber Pro
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Elige el área, define el nombre y el sistema generará el código de
              acceso único de tu curso.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className={`space-y-4 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
          {/* Área de Saber Pro (catálogo del backend, obligatorio) */}
          <div className="space-y-1.5">
            <Label htmlFor="area_id" className={`${paletaSaberPro.titulo}`}>
              Área de Saber Pro *
            </Label>
            <Controller
              control={control}
              name="area_id"
              render={({ field }) => (
                <Select
                  items={areas.map((area) => ({ value: String(area.id), label: area.nombre }))}
                  value={field.value}
                  onValueChange={field.onChange}
                >
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Selecciona el área" />
                  </SelectTrigger>
                  <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                    {areas.map((area) => (
                      <SelectItem key={area.id} value={String(area.id)} className={selectItemLargo}>
                        {area.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.area_id && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.area_id.message}</p>
            )}
          </div>

          {/* Nombre del curso */}
          <div className="space-y-1.5">
            <Label htmlFor="nombre" className={`${paletaSaberPro.titulo}`}>
              Nombre del curso *
            </Label>
            <Input
              id="nombre"
              placeholder="Ej: Preparación Razonamiento Cuantitativo"
              maxLength={100}
              className="bg-white dark:bg-[#243A5E]"
              {...register('nombre')}
            />
            {errors.nombre && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.nombre.message}</p>
            )}
          </div>

          {/* Descripción opcional */}
          <div className="space-y-1.5">
            <Label htmlFor="descripcion" className={`${paletaSaberPro.titulo}`}>
              Descripción
            </Label>
            <Textarea
              id="descripcion"
              placeholder="Descripción opcional del curso"
              rows={3}
              maxLength={500}
              className="bg-white dark:bg-[#243A5E]"
              {...register('descripcion')}
            />
          </div>

          {/* Pie: nota de código automático + botones */}
          <div className={`border-t pt-4 ${paletaSaberPro.borde}`}>
            <p className={`flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
              <ShieldCheck className={`h-3.5 w-3.5 ${paletaSaberPro.accion}`} />
              El código de acceso se genera automáticamente (HU-17.2).
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <Button type="button" className={`${paletaSaberPro.botonNeutro}`} onClick={manejarCerrar} disabled={enviando}>
                Cancelar
              </Button>
              <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={enviando}>
                {enviando ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creando...
                  </>
                ) : (
                  <>
                    <Hash className="h-4 w-4" />
                    Crear curso
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