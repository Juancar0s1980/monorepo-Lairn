// Exámenes, Estudiantes y Analítica de un curso específico para el Docente.
//
// Muestra un header con gradiente del curso, stats globales (inscritos,
// promedio, total exámenes), y tabs para alternar entre exámenes, estudiantes
// y analítica.
//
// Cada tab es un componente separado en ./componentes/ para mejor legibilidad.
// Los datos se cargan aquí y se pasan como props a cada tab.
//
// Obtiene datos en paralelo de:
//   - /examenes/examenes/ (filtrado por curso)
//   - /analitica/curso/{id}/resumen/
//   - /analitica/curso/{id}/patrones/

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  FileText,
  Users,
  BarChart3,
  Loader2,
  MoreVertical,
  Pencil,
  Target,
  Trash2,
  BookOpen,
  Code2,
  Lightbulb,
} from 'lucide-react'
import { toast } from 'sonner'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { TabExamenesDocente } from './componentes/tab-examenes-docente'
import { TabEstudiantesDocente } from './componentes/tab-estudiantes-docente'
import { TabAnaliticaDocente } from './componentes/tab-analitica-docente'
import { TabObjetivosDocente } from './componentes/tab-objetivos-docente'
import { TabLaboratoriosDocente } from './componentes/tab-laboratorios-docente'
import { TabCampoEstudioDocente } from './componentes/tab-campo-estudio-docente'
import { GatePlanAulaDocente } from './componentes/gate-plan-aula-docente'
import type { Examen } from '@/types/examen'
import type { ResumenCursoDocente, PatronesCurso } from '@/types/analitica'

// Modelo de curso tal como lo devuelve el backend.
interface Curso {
  id: number
  nombre: string
  descripcion: string
  codigo: string
  creado_en: string
  campo_estudio_habilitado: boolean
  plan_aula_cargado: boolean
}

// Esquema de validación para actualizar los datos del curso.
const esquemaActualizarCurso = z.object({
  nombre: z.string().min(1, 'El nombre es obligatorio').max(100, 'Máximo 100 caracteres'),
  descripcion: z.string().optional(),
})

type DatosActualizarCurso = z.infer<typeof esquemaActualizarCurso>

export default function PaginaExamenesCursoDocente() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Estado del curso (para editar nombre/descripcion y evitar depender solo de analítica).
  const [curso, setCurso] = useState<Curso | null>(null)
  const [cargandoCurso, setCargandoCurso] = useState(true)

  // Estado de diálogos.
  const [dialogoEditarAbierto, setDialogoEditarAbierto] = useState(false)
  const [dialogoEliminarAbierto, setDialogoEliminarAbierto] = useState(false)
  const [actualizando, setActualizando] = useState(false)
  const [eliminando, setEliminando] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatosActualizarCurso>({
    resolver: zodResolver(esquemaActualizarCurso),
    defaultValues: {
      nombre: '',
      descripcion: '',
    },
  })

  // Estado de exámenes.
  const [examenes, setExamenes] = useState<Examen[]>([])
  const [cargandoExamenes, setCargandoExamenes] = useState(true)

  // Estado de resumen (analítica).
  const [resumen, setResumen] = useState<ResumenCursoDocente | null>(null)
  const [cargandoResumen, setCargandoResumen] = useState(true)

  // Estado de patrones (analítica detallada).
  const [patrones, setPatrones] = useState<PatronesCurso | null>(null)
  const [cargandoPatrones, setCargandoPatrones] = useState(true)

  // Carga los datos del curso (nombre/descripcion/código) para acciones de edición.
  useEffect(() => {
    if (!id) return

    const cargarCurso = async () => {
      try {
        const { data } = await api.get<Curso[]>('/examenes/cursos/')
        const encontrado = data.find((c) => c.id === Number(id)) ?? null
        setCurso(encontrado)
        if (encontrado) {
          reset({
            nombre: encontrado.nombre,
            descripcion: encontrado.descripcion ?? '',
          })
        }
      } catch {
        toast.error('No se pudieron cargar los datos del curso')
      } finally {
        setCargandoCurso(false)
      }
    }

    cargarCurso()
  }, [id, reset])

  // Carga los exámenes del curso al montar el componente.
  useEffect(() => {
    const cargarExamenes = async () => {
      try {
        const { data } = await api.get<Examen[]>('/examenes/examenes/')
        const examenesDelCurso = data.filter(
          (examen) => examen.curso === Number(id)
        )
        setExamenes(examenesDelCurso)
      } catch {
        toast.error('No se pudieron cargar los exámenes')
      } finally {
        setCargandoExamenes(false)
      }
    }
    cargarExamenes()
  }, [id])

  // Carga el resumen del curso (analítica) al montar el componente.
  useEffect(() => {
    const cargarResumen = async () => {
      try {
        const { data } = await api.get<ResumenCursoDocente>(
          `/analitica/curso/${id}/resumen/`
        )
        setResumen(data)
      } catch {
        // Si falla la analítica, se muestra sin stats.
      } finally {
        setCargandoResumen(false)
      }
    }
    cargarResumen()
  }, [id])

  // Carga los patrones del curso (analítica detallada) al montar el componente.
  useEffect(() => {
    const cargarPatrones = async () => {
      try {
        const { data } = await api.get<PatronesCurso>(
          `/analitica/curso/${id}/patrones/`
        )
        setPatrones(data)
      } catch {
        // Si falla la analítica, se muestra sin stats.
      } finally {
        setCargandoPatrones(false)
      }
    }
    cargarPatrones()
  }, [id])

  // Agrega el examen creado a la lista sin recargar.
  const agregarExamen = (examen: Examen) => {
    setExamenes((prev) => [examen, ...prev])
  }

  // Actualiza un examen en la lista local sin recargar.
  const actualizarExamenEnLista = (examenActualizado: Examen) => {
    setExamenes((prev) =>
      prev.map((e) => (e.id === examenActualizado.id ? examenActualizado : e))
    )
  }

  // Elimina un examen de la lista local sin recargar.
  const eliminarExamenDeLista = (examenId: number) => {
    setExamenes((prev) => prev.filter((e) => e.id !== examenId))
  }

  // Elimina un estudiante del resumen local.
  const eliminarEstudianteDelResumen = (estudianteId: number) => {
    setResumen((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        total_inscritos: prev.total_inscritos - 1,
        estudiantes: prev.estudiantes.filter(
          (e) => e.estudiante_id !== estudianteId
        ),
      }
    })
  }

  // Actualiza los datos del curso (PATCH).
  const actualizarCurso = async (datos: DatosActualizarCurso) => {
    if (!id) return
    setActualizando(true)
    try {
      const { data } = await api.patch<Curso>(`/examenes/cursos/${id}/`, {
        nombre: datos.nombre,
        descripcion: datos.descripcion || '',
      })
      toast.success('Curso actualizado')
      setCurso(data)

      // Si la analítica está cargada, el nombre del header viene de `resumen.curso`.
      // Lo actualizamos localmente para reflejar cambios sin recargar.
      setResumen((prev) => (prev ? { ...prev, curso: data.nombre } : prev))

      setDialogoEditarAbierto(false)
      reset({ nombre: data.nombre, descripcion: data.descripcion ?? '' })
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
      }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo actualizar el curso')
      }
    } finally {
      setActualizando(false)
    }
  }

  // Elimina el curso (DELETE) y redirige.
  const eliminarCurso = async () => {
    if (!id) return
    setEliminando(true)
    try {
      await api.delete(`/examenes/cursos/${id}/`)
      toast.success('Curso eliminado')
      navigate('/mis-cursos')
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
      }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo eliminar el curso')
      }
    } finally {
      setEliminando(false)
    }
  }

  // Estado de carga general: spinner centrado.
  if (cargandoExamenes || cargandoResumen || cargandoCurso) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const nombreCurso = curso?.nombre || resumen?.curso || 'Curso'
  const codigoCurso = curso?.codigo || resumen?.codigo

  // Bloquea todo el curso hasta que se suba el plan de aula (solo aplica a cursos nuevos:
  // los existentes quedan exentos con plan_aula_cargado=true por la migración de backfill).
  if (curso && !curso.plan_aula_cargado) {
    return (
      <div className="space-y-6">
        <EncabezadoGradiente
          titulo={nombreCurso}
          subtitulo="Gestión de exámenes y estudiantes"
          volverA="/mis-cursos"
          volverTexto="Volver a mis cursos"
          badgeTexto={codigoCurso}
        />
        <GatePlanAulaDocente
          cursoId={id!}
          nombreCurso={nombreCurso}
          onCargado={() => setCurso({ ...curso, plan_aula_cargado: true })}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header con gradiente del curso */}
      <EncabezadoGradiente
        titulo={nombreCurso}
        subtitulo="Gestión de exámenes y estudiantes"
        volverA="/mis-cursos"
        volverTexto="Volver a mis cursos"
        badgeTexto={codigoCurso}
        acciones={
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="text-white/80 hover:text-white hover:bg-white/10"
                  aria-label="Acciones del curso"
                />
              }
            >
              <MoreVertical className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-44">
              <DropdownMenuItem
                onClick={() => {
                  reset({
                    nombre: curso?.nombre || resumen?.curso || 'Curso',
                    descripcion: curso?.descripcion ?? '',
                  })
                  setDialogoEditarAbierto(true)
                }}
              >
                <Pencil className="h-4 w-4" />
                Editar curso
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onClick={() => setDialogoEliminarAbierto(true)}
              >
                <Trash2 className="h-4 w-4" />
                Eliminar curso
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />

      {/* Diálogo para editar curso */}
      <Dialog
        open={dialogoEditarAbierto}
        onOpenChange={(open) => !open && setDialogoEditarAbierto(false)}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader className="-mx-4 -mt-4 rounded-t-xl border-b bg-primary/5 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle>Editar Curso</DialogTitle>
                <DialogDescription>
                  Actualiza el nombre y la descripción del curso
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <form
            onSubmit={handleSubmit(actualizarCurso)}
            className="space-y-4"
          >
            <div className="space-y-1.5">
              <Label htmlFor="nombre">Nombre *</Label>
              <Input
                id="nombre"
                placeholder="Ej: Programación I"
                maxLength={100}
                {...register('nombre')}
              />
              {errors.nombre && (
                <p className="text-xs text-destructive">{errors.nombre.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="descripcion">Descripción</Label>
              <Textarea
                id="descripcion"
                placeholder="Descripción del curso"
                rows={3}
                {...register('descripcion')}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogoEditarAbierto(false)}
                disabled={actualizando}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={actualizando}>
                {actualizando ? (
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
        </DialogContent>
      </Dialog>

      {/* Diálogo de confirmación para eliminar curso */}
      <Dialog
        open={dialogoEliminarAbierto}
        onOpenChange={(open) => !open && setDialogoEliminarAbierto(false)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Eliminar Curso</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que deseas eliminar el curso{' '}
              <span className="font-medium text-foreground">{nombreCurso}</span>
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
              onClick={eliminarCurso}
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

      {/* Tabs de navegación */}
      <Tabs defaultValue="examenes">
        <TabsList>
          <TabsTrigger value="examenes">
            <FileText className="h-4 w-4" />
            Exámenes
          </TabsTrigger>
          <TabsTrigger value="objetivos">
            <Target className="h-4 w-4" />
            Objetivos
          </TabsTrigger>
          <TabsTrigger value="laboratorios">
            <Code2 className="h-4 w-4" />
            Laboratorios
          </TabsTrigger>
          <TabsTrigger value="analitica">
            <BarChart3 className="h-4 w-4" />
            Analítica
          </TabsTrigger>
          <TabsTrigger value="estudiantes">
            <Users className="h-4 w-4" />
            Estudiantes
          </TabsTrigger>
          <TabsTrigger value="campo-estudio">
            <Lightbulb className="h-4 w-4" />
            Campo de Estudio
          </TabsTrigger>
        </TabsList>

        {/* Tab de Exámenes */}
        <TabsContent value="examenes">
          <TabExamenesDocente
            examenes={examenes}
            cargandoExamenes={cargandoExamenes}
            cursoId={Number(id)}
            onExamenCreado={agregarExamen}
            onExamenActualizado={actualizarExamenEnLista}
            onExamenEliminado={eliminarExamenDeLista}
          />
        </TabsContent>

        {/* Tab de Objetivos */}
        <TabsContent value="objetivos">
          <TabObjetivosDocente cursoId={id!} />
        </TabsContent>

        {/* Tab de Laboratorios */}
        <TabsContent value="laboratorios">
          <TabLaboratoriosDocente cursoId={id!} />
        </TabsContent>

        {/* Tab de Estudiantes */}
        <TabsContent value="estudiantes">
          <TabEstudiantesDocente
            resumen={resumen}
            cargandoResumen={cargandoResumen}
            cursoId={id!}
            onEstudianteEliminado={eliminarEstudianteDelResumen}
          />
        </TabsContent>

        {/* Tab de Analítica */}
        <TabsContent value="analitica">
          <TabAnaliticaDocente
            resumen={resumen}
            patrones={patrones}
            cargandoPatrones={cargandoPatrones}
            cargandoResumen={cargandoResumen}
            cursoId={id!}
          />
        </TabsContent>

        {/* Tab de Campo de Estudio */}
        <TabsContent value="campo-estudio">
          <TabCampoEstudioDocente
            cursoId={id!}
            habilitado={curso?.campo_estudio_habilitado ?? false}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
