// Modal para crear un nuevo examen.
// Utiliza React Hook Form + Zod para validación del formulario.
// Campos: curso (del param), titulo, tema, tiempo, num_preguntas,
//   retroalimentacion, es_guiado, dificultad_inicial, modo, max_intentos, max_preguntas.
// Envía POST a /examenes/examenes/ y notifica al componente padre tras crear.

import { useEffect, useState } from 'react'
import { useForm, Controller, useWatch } from 'react-hook-form'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Check, Loader2, FileText, Info, Target } from 'lucide-react'
import { toast } from 'sonner'
import type { Examen, ObjetivoCurso } from '@/types/examen'

// Tooltip de ayuda para cada campo.
function Ayuda({ texto }: { texto: string }) {
  return (
    <Tooltip>
      <TooltipTrigger className="inline-flex items-center justify-center cursor-help">
        <Info className="h-3.5 w-3.5 text-muted-foreground/60" />
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs text-xs">
        {texto}
      </TooltipContent>
    </Tooltip>
  )
}

// Esquema de validación con Zod.
const esquemaCrearExamen = z.object({
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
}).refine(
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
).refine(
  (datos) => {
    if (datos.modo === 'maestria' && datos.max_preguntas && datos.num_preguntas) {
      return Number(datos.max_preguntas) >= Number(datos.num_preguntas)
    }
    return true
  },
  {
    message: 'Max. Preguntas debe ser mayor o igual a N° Preguntas en modo Maestría',
    path: ['max_preguntas'],
  }
)

type DatosCrearExamen = z.infer<typeof esquemaCrearExamen>

interface ModalCrearExamenProps {
  abierta: boolean
  onCerrar: () => void
  onExamenCreado: (examen: Examen) => void
  cursoId: number
}

export function ModalCrearExamen({
  abierta,
  onCerrar,
  onExamenCreado,
  cursoId,
}: ModalCrearExamenProps) {
  const [enviando, setEnviando] = useState(false)

  // Objetivos del curso disponibles para anclar el examen (selección opcional).
  const [objetivosCurso, setObjetivosCurso] = useState<ObjetivoCurso[]>([])
  const [objetivosSeleccionados, setObjetivosSeleccionados] = useState<Set<number>>(new Set())

  // Carga los objetivos del curso al abrir la modal (para poblar el selector).
  useEffect(() => {
    if (!abierta) return
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<ObjetivoCurso[]>(
          `/examenes/cursos/${cursoId}/objetivos/`,
          { signal: controlador.signal }
        )
        setObjetivosCurso(data)
      } catch {
        // Sin objetivos disponibles: el selector simplemente no se muestra.
      }
    }
    cargar()
    return () => controlador.abort()
  }, [abierta, cursoId])

  const alternarObjetivo = (id: number) => {
    setObjetivosSeleccionados((prev) => {
      const nuevo = new Set(prev)
      if (nuevo.has(id)) nuevo.delete(id)
      else nuevo.add(id)
      return nuevo
    })
  }

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<DatosCrearExamen>({
    resolver: zodResolver(esquemaCrearExamen),
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

  // Envía el formulario al backend.
  const onSubmit = async (datos: DatosCrearExamen) => {
    setEnviando(true)
    try {
      const { data } = await api.post<Examen>('/examenes/examenes/', {
        curso: cursoId,
        titulo: datos.titulo,
        tema: datos.tema,
        tiempo: Number(datos.tiempo),
        num_preguntas: Number(datos.num_preguntas),
        retroalimentacion: datos.retroalimentacion,
        es_guiado: datos.es_guiado,
        dificultad_inicial: Number(datos.dificultad_inicial),
        modo: datos.modo,
        max_intentos: datos.max_intentos ? Number(datos.max_intentos) : 1,
        fecha_limite: datos.fecha_limite ? new Date(datos.fecha_limite).toISOString() : null,
        max_preguntas:
          datos.modo === 'maestria' && datos.max_preguntas
            ? Number(datos.max_preguntas)
            : 0,
        objetivos: Array.from(objetivosSeleccionados),
      })
      toast.success('Examen creado exitosamente')
      onExamenCreado(data)
      reset()
      setObjetivosSeleccionados(new Set())
      onCerrar()
    } catch {
      toast.error('No se pudo crear el examen')
    } finally {
      setEnviando(false)
    }
  }

  // Resetea el formulario al cerrar.
  const manejarCerrar = () => {
    reset()
    setObjetivosSeleccionados(new Set())
    onCerrar()
  }



  return (
    <Dialog open={abierta} onOpenChange={(open) => !open && manejarCerrar()}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header con icono y fondo diferenciado */}
        <DialogHeader className="-mx-4 -mt-4 rounded-t-xl border-b bg-primary/5 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Crear Examen</DialogTitle>
              <DialogDescription>
                Completa los datos para crear un nuevo examen
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Campo título */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label htmlFor="titulo">Título *</Label>
              <Ayuda texto="Título del examen que verán los estudiantes." />
            </div>
            <Input
              id="titulo"
              placeholder="Ej: Parcial 1 - Introducción a la Programación"
              {...register('titulo')}
            />
            {errors.titulo && (
              <p className="text-xs text-destructive">
                {errors.titulo.message}
              </p>
            )}
          </div>

          {/* Campo tema */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label htmlFor="tema">Tema *</Label>
              <Ayuda texto="Tema sobre el que la IA generará las preguntas. Mientras más específico, mejor." />
            </div>
            <Input
              id="tema"
              placeholder="Ej: Variables, tipos de datos y operadores"
              {...register('tema')}
            />
            {errors.tema && (
              <p className="text-xs text-destructive">
                {errors.tema.message}
              </p>
            )}
          </div>

          {/* Selector de objetivos del curso (solo si el curso tiene objetivos) */}
          {objetivosCurso.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label>Objetivos a evaluar</Label>
                <Ayuda texto="La IA generará cada pregunta evaluando exactamente uno de los objetivos marcados. Si no marcas ninguno, usará solo el tema." />
              </div>
              <div className="max-h-36 space-y-1.5 overflow-y-auto rounded-lg border p-2">
                {objetivosCurso.map((objetivo) => (
                  <button
                    key={objetivo.id}
                    type="button"
                    onClick={() => alternarObjetivo(objetivo.id)}
                    className={`flex w-full items-start gap-2 rounded-md p-2 text-left text-xs transition-colors ${
                      objetivosSeleccionados.has(objetivo.id)
                        ? 'bg-primary/5 text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50'
                    }`}
                  >
                    <span
                      className={`mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border ${
                        objetivosSeleccionados.has(objetivo.id)
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-input'
                      }`}
                    >
                      {objetivosSeleccionados.has(objetivo.id) && <Check className="h-2.5 w-2.5" />}
                    </span>
                    {objetivo.descripcion}
                  </button>
                ))}
              </div>
              {objetivosSeleccionados.size > 0 && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Target className="h-3 w-3" />
                  {objetivosSeleccionados.size} objetivo(s) anclado(s) a este examen
                </p>
              )}
            </div>
          )}

          {/* Fila: tiempo y número de preguntas */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="tiempo">Tiempo (min) *</Label>
                <Ayuda texto="Duración del examen en minutos." />
              </div>
              <Input
                id="tiempo"
                type="number"
                placeholder="60"
                {...register('tiempo')}
              />
              {errors.tiempo && (
                <p className="text-xs text-destructive">
                  {errors.tiempo.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="num_preguntas">N° Preguntas *</Label>
                <Ayuda texto="Cantidad de preguntas del examen. En modo Maestría es el mínimo de preguntas." />
              </div>
              <Input
                id="num_preguntas"
                type="number"
                placeholder="10"
                {...register('num_preguntas')}
              />
              {errors.num_preguntas && (
                <p className="text-xs text-destructive">
                  {errors.num_preguntas.message}
                </p>
              )}
            </div>
          </div>

          {/* Fila: dificultad y modo */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label>Dificultad *</Label>
                <Ayuda texto="Dificultad inicial del examen. El motor adaptativo ajustará según el rendimiento." />
              </div>
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
              <div className="flex items-center gap-1.5">
                <Label>Modo *</Label>
                <Ayuda texto="Fijo = número exacto de preguntas. Maestría = continúa hasta dominar el tema." />
              </div>
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

          {/* Campo: max_intentos */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label htmlFor="max_intentos">Max. Intentos</Label>
              <Ayuda texto="Cuántas veces puede intentarlo. 0 = sin límite. Ej: 3" />
            </div>
            <Input
              id="max_intentos"
              type="number"
              placeholder="1"
              {...register('max_intentos')}
            />
            {errors.max_intentos && (
              <p className="text-xs text-destructive">
                {errors.max_intentos.message}
              </p>
            )}
          </div>

          {/* Campo: fecha_limite */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label htmlFor="fecha_limite">Fecha límite</Label>
              <Ayuda texto="Después de esta fecha ya no se pueden empezar intentos nuevos. Vacío = sin límite. Un examen ya en curso no se ve afectado." />
            </div>
            <Input
              id="fecha_limite"
              type="datetime-local"
              {...register('fecha_limite')}
            />
          </div>

          {/* Campo: max_preguntas (solo en modo maestria) */}
          {modoSeleccionado === 'maestria' && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="max_preguntas">Max. Preguntas</Label>
                <Ayuda texto="Límite máximo de preguntas antes de terminar, aunque no haya dominado el tema." />
              </div>
              <Input
                id="max_preguntas"
                type="number"
                placeholder="20"
                {...register('max_preguntas')}
              />
              {errors.max_preguntas && (
                <p className="text-xs text-destructive">
                  {errors.max_preguntas.message}
                </p>
              )}
            </div>
          )}

          {/* Fila: switches */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-1.5">
                  <Label>Retroalimentación</Label>
                  <Ayuda texto="Si el estudiante ve si acertó o no después de cada respuesta, con explicación." />
                </div>
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
                <div className="flex items-center gap-1.5">
                  <Label>Modo guiado</Label>
                  <Ayuda texto="Si la IA da una explicación corta antes de cada pregunta para guiar al estudiante." />
                </div>
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

          {/* Footer con botones */}
          <DialogFooter>
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
                'Crear Examen'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
