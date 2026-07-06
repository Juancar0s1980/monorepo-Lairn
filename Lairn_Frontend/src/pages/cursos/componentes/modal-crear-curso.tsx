// Modal para crear un nuevo curso.
// Utiliza React Hook Form + Zod para validación del formulario.
// Campos: nombre (requerido, máx 100) y descripción (opcional).
// Envía POST a /examenes/cursos/ y notifica al componente padre tras crear.

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
import { Textarea } from '@/components/ui/textarea'
import { Loader2, BookOpen, Hash } from 'lucide-react'
import { toast } from 'sonner'

// Esquema de validación con Zod.
const esquemaCrearCurso = z.object({
  nombre: z
    .string()
    .min(1, 'El nombre es obligatorio')
    .max(100, 'Máximo 100 caracteres'),
  descripcion: z.string().optional(),
})

type DatosCrearCurso = z.infer<typeof esquemaCrearCurso>

// Modelo de curso que devuelve el backend al crear.
interface Curso {
  id: number
  nombre: string
  descripcion: string
  codigo: string
  creado_en: string
}

interface ModalCrearCursoProps {
  abierta: boolean
  onCerrar: () => void
  onCursoCreado: (curso: Curso) => void
}

export function ModalCrearCurso({
  abierta,
  onCerrar,
  onCursoCreado,
}: ModalCrearCursoProps) {
  const [enviando, setEnviando] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatosCrearCurso>({
    resolver: zodResolver(esquemaCrearCurso),
    defaultValues: {
      nombre: '',
      descripcion: '',
    },
  })

  // Envía el formulario al backend.
  const onSubmit = async (datos: DatosCrearCurso) => {
    setEnviando(true)
    try {
      const { data } = await api.post<Curso>('/examenes/cursos/', {
        nombre: datos.nombre,
        descripcion: datos.descripcion || '',
      })
      toast.success('Curso creado exitosamente')
      onCursoCreado(data)
      reset()
      onCerrar()
    } catch {
      toast.error('No se pudo crear el curso')
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
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Crear Curso</DialogTitle>
              <DialogDescription>
                Completa los datos para crear un nuevo curso
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Campo nombre */}
          <div className="space-y-1.5">
            <Label htmlFor="nombre">Nombre *</Label>
            <Input
              id="nombre"
              placeholder="Ej: Programación I"
              maxLength={100}
              {...register('nombre')}
            />
            {errors.nombre && (
              <p className="text-xs text-destructive">
                {errors.nombre.message}
              </p>
            )}
          </div>

          {/* Campo descripción */}
          <div className="space-y-1.5">
            <Label htmlFor="descripcion">Descripción</Label>
            <Textarea
              id="descripcion"
              placeholder="Descripción opcional del curso"
              rows={3}
              {...register('descripcion')}
            />
          </div>

          {/* Footer con nota de código automático y botones */}
          <DialogFooter>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground sm:mr-auto">
              <Hash className="h-3.5 w-3.5" />
              El código se genera automáticamente
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
                  Creando...
                </div>
              ) : (
                'Crear Curso'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
