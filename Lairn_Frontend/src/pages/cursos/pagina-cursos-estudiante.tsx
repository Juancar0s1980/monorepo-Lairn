// Vista de cursos para el Estudiante.
// Muestra los cursos en los que está inscrito el estudiante usando CardCurso.
// Permite inscribirse a un curso mediante código.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BookOpen, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { ModalInscribirCurso } from './componentes/modal-inscribir-curso'
import { CardCursoEstudiante } from '@/components/card-curso-estudiante'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import type { AvanceCurso } from '@/types/analitica'
import type { Examen } from '@/types/examen'

// Modelo de curso tal como lo devuelve el backend.
interface Curso {
  id: number
  nombre: string
  docente: string
  descripcion: string
}

export default function PaginaCursosEstudiante() {
  // Estado de cursos.
  const [cursos, setCursos] = useState<Curso[]>([])
  const [cargando, setCargando] = useState(true)

  // Estado de datos enriquecidos por curso.
  const [avances, setAvances] = useState<Map<number, AvanceCurso>>(new Map())
  const [examenesPorCurso, setExamenesPorCurso] = useState<Map<number, Examen[]>>(new Map())

  // Estado del modal de inscripción.
  const [modalInscribir, setModalInscribir] = useState(false)

  // Carga los cursos del estudiante.
  const cargarCursos = async () => {
    setCargando(true)
    try {
      const { data } = await api.get<Curso[]>('/examenes/mis-cursos/')
      console.log('Cursos recibidos:', data)
      setCursos(data)
      // Después de cargar cursos, obtener analytics y exámenes.
      await cargarDatosEnriquecidos(data)
    } catch {
      toast.error('No se pudieron cargar los cursos')
    } finally {
      setCargando(false)
    }
  }

  // Carga analytics y exámenes para cada curso en paralelo.
  const cargarDatosEnriquecidos = async (listaCursos: Curso[]) => {
    const nuevosAvances = new Map<number, AvanceCurso>()
    const nuevosExamenes = new Map<number, Examen[]>()

    const promesas = listaCursos.map(async (curso) => {
      const [resAvance, resExamenes] = await Promise.allSettled([
        api.get<AvanceCurso>(`/analitica/mi-avance/curso/${curso.id}/`),
        api.get<Examen[]>(`/examenes/mis-cursos/${curso.id}/examenes/`),
      ])

      if (resAvance.status === 'fulfilled') {
        nuevosAvances.set(curso.id, resAvance.value.data)
      }
      if (resExamenes.status === 'fulfilled') {
        nuevosExamenes.set(curso.id, resExamenes.value.data)
      }
    })

    await Promise.allSettled(promesas)

    setAvances(nuevosAvances)
    setExamenesPorCurso(nuevosExamenes)
  }

  // Carga los cursos al montar el componente.
  useEffect(() => {
    const controlador = new AbortController()

    const cargarCursosInicial = async () => {
      try {
        const { data } = await api.get<Curso[]>('/examenes/mis-cursos/', {
          signal: controlador.signal,
        })
        setCursos(data)
        if (!controlador.signal.aborted) {
          await cargarDatosEnriquecidos(data)
        }
      } catch {
        if (!controlador.signal.aborted) {
          toast.error('No se pudieron cargar los cursos')
        }
      } finally {
        if (!controlador.signal.aborted) {
          setCargando(false)
        }
      }
    }
    cargarCursosInicial()

    return () => controlador.abort()
  }, [])

  // Recarga los cursos después de una inscripción exitosa.
  const manejarInscripcionExitosa = () => {
    setCargando(true)
    cargarCursos()
  }

  // Estado de carga: skeleton cards.
  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="animate-pulse space-y-2">
            <div className="h-7 w-40 rounded bg-muted" />
            <div className="h-4 w-56 rounded bg-muted" />
          </div>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <div className="h-24 animate-pulse bg-muted" />
              <CardContent className="p-5 space-y-3">
                <div className="animate-pulse space-y-2">
                  <div className="h-5 w-32 rounded bg-muted" />
                  <div className="h-3 w-20 rounded bg-muted" />
                </div>
                <div className="h-4 w-full rounded bg-muted animate-pulse" />
                <div className="h-2 w-full rounded bg-muted animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Panel del estudiante"
        titulo="Mis Cursos"
        subtitulo="Accede a los exámenes y revisa tu progreso"
        accion={
          <Button onClick={() => setModalInscribir(true)}>
            <Plus className="h-4 w-4" />
            Inscribirme a un Curso
          </Button>
        }
      />

      {/* Estado vacío */}
      {cursos.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <BookOpen className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No estás inscrito en ningún curso
          </p>
          <p className="text-xs text-muted-foreground/70">
            Usa el botón "Inscribirme a un Curso" con el código de tu docente
          </p>
        </div>
      )}

      {/* Grid de cards de cursos */}
      {cursos.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {cursos.map((curso) => {
            const avance = avances.get(curso.id)
            const examenes = examenesPorCurso.get(curso.id) ?? []

            return (
              <CardCursoEstudiante
                key={curso.id}
                id={curso.id}
                nombre={curso.nombre}
                descripcion={curso.descripcion}
                docente={curso.docente}
                examenesRendidos={avance?.total_examenes_presentados ?? 0}
                totalExamenes={examenes.length}
                notaPromedio={avance?.nota_promedio}
              />
            )
          })}
        </div>
      )}

      {/* Modal para inscribirse a un curso */}
      <ModalInscribirCurso
        abierta={modalInscribir}
        onCerrar={() => setModalInscribir(false)}
        onInscripcionExitosa={manejarInscripcionExitosa}
      />
    </div>
  )
}
