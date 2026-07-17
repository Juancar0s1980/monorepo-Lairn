// Tab de exámenes para el docente.
//
// Muestra un grid de cards con los exámenes del curso, botón para crear
// nuevo examen y estado vacío cuando no hay exámenes.

import { useState } from 'react'
import { useForm, Controller, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  FileText,
  Clock,
  HelpCircle,
  Plus,
  RotateCw,
  MoreVertical,
  Pencil,
  Trash2,
  Loader2,
  CalendarClock,
} from 'lucide-react'
import { toast } from 'sonner'
import { ModalCrearExamen } from './modal-crear-examen'
import { dificultadConfig } from '../utilidades'
import type { Examen } from '@/types/examen'

// Esquema de validación para editar examen.
// Replica las reglas del modal de creación: tipos string en inputs y coerción a number al enviar.
const esquemaEditarExamen = z
  .object({
    titulo: z.string().min(1, 'El título es obligatorio'),
    tema: z.string().min(1, 'El tema es obligatorio'),
    tiempo: z.string().min(1, 'El tiempo es obligatorio'),
    num_preguntas: z.string().min(1, 'El número de preguntas es obligatorio'),
    max_intentos: z.string().optional(),
    fecha_limite: z.string().optional(),
    max_preguntas: z.string().optional(),
    dificultad_inicial: z.enum(['1', '2', '3']),
    modo: z.enum(['fijo', 'maestria']),
    retroalimentacion: z.boolean(),
    es_guiado: z.boolean(),
  })
  .refine(
    (datos) => {
      if (datos.max_intentos && datos.max_intentos !== '') {
        const val = Number(datos.max_intentos)
        return val >= 0 && val <= 10
      }
      return true
    },
    {
      message: 'Max. Intentos debe ser entre 0 (ilimitado) y 10',
      path: ['max_intentos'],
    }
  )
  .refine(
    (datos) => {
      if (
        datos.modo === 'maestria' &&
        datos.max_preguntas &&
        datos.num_preguntas
      ) {
        return Number(datos.max_preguntas) >= Number(datos.num_preguntas)
      }
      return true
    },
    {
      message:
        'Max. Preguntas debe ser mayor o igual a N° Preguntas en modo Maestría',
      path: ['max_preguntas'],
    }
  )

type DatosEditarExamen = z.infer<typeof esquemaEditarExamen>

// Convierte un ISO (respuesta del backend) al formato que espera <input type="datetime-local">.
function isoAFechaLocal(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

interface TabExamenesDocenteProps {
  examenes: Examen[]
  cargandoExamenes: boolean
  cursoId: number
  onExamenCreado: (examen: Examen) => void
  onExamenActualizado: (examen: Examen) => void
  onExamenEliminado: (examenId: number) => void
}

export function TabExamenesDocente({
  examenes,
  cargandoExamenes,
  cursoId,
  onExamenCreado,
  onExamenActualizado,
  onExamenEliminado,
}: TabExamenesDocenteProps) {
  const [modalCrearExamen, setModalCrearExamen] = useState(false)

  // Estado de edición/eliminación.
  const [examenIdAccion, setExamenIdAccion] = useState<number | null>(null)
  const [dialogoEditarAbierto, setDialogoEditarAbierto] = useState(false)
  const [dialogoEliminarAbierto, setDialogoEliminarAbierto] = useState(false)
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [eliminando, setEliminando] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<DatosEditarExamen>({
    resolver: zodResolver(esquemaEditarExamen),
    defaultValues: {
      titulo: '',
      tema: '',
      tiempo: '',
      num_preguntas: '',
      max_intentos: '',
      fecha_limite: '',
      max_preguntas: '',
      dificultad_inicial: '1',
      modo: 'fijo',
      retroalimentacion: false,
      es_guiado: false,
    },
  })

  // Observa el modo seleccionado sin usar `watch()` (evita warnings del React Compiler).
  const modoSeleccionado = useWatch({ control, name: 'modo' })

  // Carga detalle del examen y abre el diálogo de edición.
  const abrirEditar = async (examenId: number) => {
    setExamenIdAccion(examenId)
    setDialogoEditarAbierto(true)
    setCargandoDetalle(true)
    try {
      const { data } = await api.get<Examen>(`/examenes/examenes/${examenId}/`)
      reset({
        titulo: data.titulo ?? '',
        tema: data.tema ?? '',
        tiempo: String(data.tiempo ?? ''),
        num_preguntas: String(data.num_preguntas ?? ''),
        max_intentos: String(data.max_intentos ?? ''),
        fecha_limite: isoAFechaLocal(data.fecha_limite),
        max_preguntas: String(data.max_preguntas ?? ''),
        dificultad_inicial: String(data.dificultad_inicial ?? 1) as '1' | '2' | '3',
        modo: (data.modo ?? 'fijo') as 'fijo' | 'maestria',
        retroalimentacion: !!data.retroalimentacion,
        es_guiado: !!data.es_guiado,
      })
    } catch {
      toast.error('No se pudo cargar el examen')
      setDialogoEditarAbierto(false)
      setExamenIdAccion(null)
    } finally {
      setCargandoDetalle(false)
    }
  }

  const onSubmitEditar = async (datos: DatosEditarExamen) => {
    if (!examenIdAccion) return
    setGuardando(true)
    try {
      const payload = {
        curso: cursoId,
        titulo: datos.titulo,
        tema: datos.tema,
        tiempo: Number(datos.tiempo),
        num_preguntas: Number(datos.num_preguntas),
        retroalimentacion: datos.retroalimentacion,
        es_guiado: datos.es_guiado,
        dificultad_inicial: Number(datos.dificultad_inicial),
        modo: datos.modo,
        // 0 es permitido y significa ilimitado.
        max_intentos:
          datos.max_intentos && datos.max_intentos !== ''
            ? Number(datos.max_intentos)
            : 0,
        fecha_limite: datos.fecha_limite ? new Date(datos.fecha_limite).toISOString() : null,
        max_preguntas:
          datos.modo === 'maestria' && datos.max_preguntas
            ? Number(datos.max_preguntas)
            : 0,
      }

      const { data } = await api.patch<Examen>(
        `/examenes/examenes/${examenIdAccion}/`,
        payload
      )
      toast.success('Examen actualizado')
      onExamenActualizado(data)
      setDialogoEditarAbierto(false)
      setExamenIdAccion(null)
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
      }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo actualizar el examen')
      }
    } finally {
      setGuardando(false)
    }
  }

  const abrirEliminar = (examenId: number) => {
    setExamenIdAccion(examenId)
    setDialogoEliminarAbierto(true)
  }

  const confirmarEliminar = async () => {
    if (!examenIdAccion) return
    setEliminando(true)
    try {
      await api.delete(`/examenes/examenes/${examenIdAccion}/`)
      toast.success('Examen eliminado')
      onExamenEliminado(examenIdAccion)
      setDialogoEliminarAbierto(false)
      setExamenIdAccion(null)
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
      }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo eliminar el examen')
      }
    } finally {
      setEliminando(false)
    }
  }

  const examenActual =
    examenIdAccion !== null
      ? examenes.find((e) => e.id === examenIdAccion) ?? null
      : null

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setModalCrearExamen(true)}>
          <Plus className="h-4 w-4" />
          Crear Examen
        </Button>
      </div>

      {/* Estado vacío de exámenes */}
      {examenes.length === 0 && !cargandoExamenes && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <FileText className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No hay exámenes en este curso
          </p>
          <p className="text-xs text-muted-foreground">
            Crea un examen para comenzar
          </p>
        </div>
      )}

      {/* Grid de cards de exámenes */}
      {examenes.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {examenes.map((examen) => {
            const dif =
              dificultadConfig[examen.dificultad_inicial] ||
              dificultadConfig[1]
            const IconoDificultad = dif.icono

            return (
              <Card
                key={examen.id}
                className="h-full flex flex-col transition-all hover:shadow-md hover:border-primary/30 group"
              >
                <CardContent className="p-5 flex flex-col flex-1 gap-3">
                  {/* Título + badge de dificultad */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-base line-clamp-1 group-hover:text-primary transition-colors">
                        {examen.titulo}
                      </h3>
                      <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
                        {examen.tema || 'Sin tema'}
                      </p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${dif.clase}`}
                      >
                        <IconoDificultad className="h-3 w-3" />
                        {dif.label}
                      </span>

                      {/* Menú de acciones por examen */}
                      <DropdownMenu>
                        <DropdownMenuTrigger
                          render={
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon-sm"
                              className="text-muted-foreground hover:text-foreground"
                              aria-label="Acciones del examen"
                            />
                          }
                        >
                          <MoreVertical className="h-4 w-4" />
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="min-w-44">
                          <DropdownMenuItem onClick={() => abrirEditar(examen.id)}>
                            <Pencil className="h-4 w-4" />
                            Editar examen
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            variant="destructive"
                            onClick={() => abrirEliminar(examen.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                            Eliminar examen
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {/* Stats compactas */}
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <HelpCircle className="h-3.5 w-3.5" />
                      <span>{examen.num_preguntas} preg.</span>
                    </div>
                    <div className="h-3 w-px bg-border" />
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{examen.tiempo} min</span>
                    </div>
                    <div className="h-3 w-px bg-border" />
                    <div className="flex items-center gap-1">
                      <RotateCw className="h-3.5 w-3.5" />
                      <span>
                        {examen.max_intentos === 0
                          ? 'Ilimitados'
                          : `${examen.max_intentos} intentos`}
                      </span>
                    </div>
                    {examen.fecha_limite && (
                      <>
                        <div className="h-3 w-px bg-border" />
                        <div className="flex items-center gap-1">
                          <CalendarClock className="h-3.5 w-3.5" />
                          <span>{new Date(examen.fecha_limite).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Espacio para alinear con el footer */}
                  <div className="mt-auto" />
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Modal para crear examen */}
      <ModalCrearExamen
        abierta={modalCrearExamen}
        onCerrar={() => setModalCrearExamen(false)}
        onExamenCreado={onExamenCreado}
        cursoId={cursoId}
      />

      {/* Diálogo para editar examen */}
      <Dialog
        open={dialogoEditarAbierto}
        onOpenChange={(open) => {
          if (!open) {
            setDialogoEditarAbierto(false)
            setExamenIdAccion(null)
          }
        }}
      >
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Examen</DialogTitle>
            <DialogDescription>
              Modifica los datos del examen y guarda los cambios
            </DialogDescription>
          </DialogHeader>

          {cargandoDetalle ? (
            <div className="flex h-[30vh] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <form
              onSubmit={handleSubmit(onSubmitEditar)}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="titulo">Título *</Label>
                <Input id="titulo" {...register('titulo')} />
                {errors.titulo && (
                  <p className="text-xs text-destructive">{errors.titulo.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="tema">Tema *</Label>
                <Input id="tema" {...register('tema')} />
                {errors.tema && (
                  <p className="text-xs text-destructive">{errors.tema.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="tiempo">Tiempo (min) *</Label>
                  <Input id="tiempo" type="number" {...register('tiempo')} />
                  {errors.tiempo && (
                    <p className="text-xs text-destructive">{errors.tiempo.message}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="num_preguntas">N° Preguntas *</Label>
                  <Input
                    id="num_preguntas"
                    type="number"
                    {...register('num_preguntas')}
                  />
                  {errors.num_preguntas && (
                    <p className="text-xs text-destructive">
                      {errors.num_preguntas.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Dificultad *</Label>
                  <Controller
                    control={control}
                    name="dificultad_inicial"
                    render={({ field }) => (
                      <Select
                        items={[
                          { value: '1', label: 'Básico' },
                          { value: '2', label: 'Intermedio' },
                          { value: '3', label: 'Avanzado' },
                        ]}
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleccionar" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">Básico</SelectItem>
                          <SelectItem value="2">Intermedio</SelectItem>
                          <SelectItem value="3">Avanzado</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Modo *</Label>
                  <Controller
                    control={control}
                    name="modo"
                    render={({ field }) => (
                      <Select
                        items={[
                          { value: 'fijo', label: 'Fijo' },
                          { value: 'maestria', label: 'Maestría' },
                        ]}
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleccionar" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="fijo">Fijo</SelectItem>
                          <SelectItem value="maestria">Maestría</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <Label htmlFor="max_intentos">Max. Intentos</Label>
                  <p className="text-xs text-muted-foreground">0 = sin limite</p>
                </div>
                <Input
                  id="max_intentos"
                  type="number"
                  placeholder="0"
                  {...register('max_intentos')}
                />
                {errors.max_intentos && (
                  <p className="text-xs text-destructive">
                    {errors.max_intentos.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <Label htmlFor="fecha_limite">Fecha límite</Label>
                  <p className="text-xs text-muted-foreground">vacío = sin límite</p>
                </div>
                <Input
                  id="fecha_limite"
                  type="datetime-local"
                  {...register('fecha_limite')}
                />
              </div>

              {modoSeleccionado === 'maestria' && (
                <div className="space-y-1.5">
                  <Label htmlFor="max_preguntas">Max. Preguntas</Label>
                  <Input
                    id="max_preguntas"
                    type="number"
                    {...register('max_preguntas')}
                  />
                  {errors.max_preguntas && (
                    <p className="text-xs text-destructive">
                      {errors.max_preguntas.message}
                    </p>
                  )}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label>Retroalimentación</Label>
                    <p className="text-xs text-muted-foreground">
                      Mostrar explicaciones
                    </p>
                  </div>
                  <Controller
                    control={control}
                    name="retroalimentacion"
                    render={({ field }) => (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {field.value ? 'Sí' : 'No'}
                        </span>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </div>
                    )}
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label>Modo guiado</Label>
                    <p className="text-xs text-muted-foreground">
                      Asistencia paso a paso
                    </p>
                  </div>
                  <Controller
                    control={control}
                    name="es_guiado"
                    render={({ field }) => (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {field.value ? 'Sí' : 'No'}
                        </span>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </div>
                    )}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogoEditarAbierto(false)}
                  disabled={guardando}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={guardando}>
                  {guardando ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Guardando...
                    </div>
                  ) : (
                    'Guardar cambios'
                  )}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Diálogo de confirmación para eliminar examen */}
      <Dialog
        open={dialogoEliminarAbierto}
        onOpenChange={(open) => {
          if (!open) {
            setDialogoEliminarAbierto(false)
            setExamenIdAccion(null)
          }
        }}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Eliminar Examen</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que deseas eliminar el examen{' '}
              <span className="font-medium text-foreground">
                {examenActual?.titulo ?? 'Examen'}
              </span>
              ? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogoEliminarAbierto(false)}
              disabled={eliminando}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={confirmarEliminar}
              disabled={eliminando}
            >
              {eliminando ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Eliminando...
                </div>
              ) : (
                'Eliminar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
