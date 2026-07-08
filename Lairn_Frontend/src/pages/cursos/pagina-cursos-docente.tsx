// Mis Cursos del Docente.
// Muestra los cursos asignados al docente autenticado en un grid de cards.
// Cada card muestra: nombre, código, descripción y stats de analítica.
// Obtiene los cursos de GET /examenes/cursos/ y analítica de /analitica/curso/{id}/resumen/.
// Permite crear nuevos cursos mediante un botón que abre una modal.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { BookOpen, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { CardCursoDocente } from '@/components/card-curso-docente'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ModalCrearCurso } from './componentes/modal-crear-curso'
import type { ResumenCursoDocente } from '@/types/analitica'

// Modelo de curso tal como lo devuelve el backend.
interface Curso {
  id: number
  nombre: string
  descripcion: string
  codigo: string
  creado_en: string
}

// Calcula stats del curso a partir del resumen de estudiantes.
function calcularStats(resumen: ResumenCursoDocente) {
  const { estudiantes } = resumen
  if (estudiantes.length === 0) {
    return { totalExamenes: 0, tasaAprobados: undefined }
  }

  // El total de exámenes es el máximo de exámenes presentados por cualquier estudiante.
  const totalExamenes = Math.max(
    ...estudiantes.map((e) => e.examenes_presentados)
  )

  // La tasa de aprobados cuenta estudiantes con nota promedio >= 3.0.
  const aprobados = estudiantes.filter((e) => e.nota_promedio >= 3.0).length
  const tasaAprobados = Math.round((aprobados / estudiantes.length) * 100)

  return { totalExamenes, tasaAprobados }
}

export default function PaginaCursosDocente() {
  const [cursos, setCursos] = useState<Curso[]>([])
  const [resumenes, setResumenes] = useState<Map<number, ResumenCursoDocente>>(
    new Map()
  )
  const [cargando, setCargando] = useState(true)
  const [modalAbierta, setModalAbierta] = useState(false)

  // Carga el resumen de cada curso en paralelo.
  const cargarResumenes = async (listaCursos: Curso[]) => {
    const nuevosResumenes = new Map<number, ResumenCursoDocente>()

    const promesas = listaCursos.map(async (curso) => {
      try {
        const { data } = await api.get<ResumenCursoDocente>(
          `/analitica/curso/${curso.id}/resumen/`
        )
        nuevosResumenes.set(curso.id, data)
      } catch {
        // Si falla la analítica de un curso, se muestra sin stats.
      }
    })

    await Promise.allSettled(promesas)
    setResumenes(nuevosResumenes)
  }

  // Carga los cursos y su resumen al montar el componente.
  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const { data } = await api.get<Curso[]>('/examenes/cursos/')
        setCursos(data)
        await cargarResumenes(data)
      } catch {
        toast.error('No se pudieron cargar los cursos')
      } finally {
        setCargando(false)
      }
    }
    cargarDatos()
  }, [])

  // Agrega el curso creado a la lista sin recargar.
  const agregarCurso = (curso: Curso) => {
    setCursos((prev) => [curso, ...prev])
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
              <div className="h-28 animate-pulse bg-muted" />
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
        eyebrow="Panel del docente"
        titulo="Mis Cursos"
        subtitulo="Cursos asignados a tu perfil docente"
        accion={
          <Button onClick={() => setModalAbierta(true)}>
            <Plus className="h-4 w-4" />
            Crear Curso
          </Button>
        }
      />

      {/* Estado vacío */}
      {cursos.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <BookOpen className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No tienes cursos asignados
          </p>
          <p className="text-xs text-muted-foreground/70">
            Crea un curso con el botón de arriba para comenzar
          </p>
        </div>
      )}

      {/* Grid de cards de cursos */}
      {cursos.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {cursos.map((curso) => {
            const resumen = resumenes.get(curso.id)
            const stats = resumen
              ? calcularStats(resumen)
              : { totalExamenes: 0, tasaAprobados: undefined }

            return (
              <CardCursoDocente
                key={curso.id}
                id={curso.id}
                nombre={curso.nombre}
                descripcion={curso.descripcion}
                codigo={curso.codigo}
                totalInscritos={resumen?.total_inscritos ?? 0}
                totalExamenes={stats.totalExamenes}
                notaPromedio={resumen?.nota_promedio_curso}
                tasaAprobados={stats.tasaAprobados}
              />
            )
          })}
        </div>
      )}

      {/* Modal para crear curso */}
      <ModalCrearCurso
        abierta={modalAbierta}
        onCerrar={() => setModalAbierta(false)}
        onCursoCreado={agregarCurso}
      />
    </div>
  )
}
