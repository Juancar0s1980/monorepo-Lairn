// Exámenes de un curso específico para el Estudiante.
//
// Muestra un header con gradiente del curso, stats globales (exámenes rendidos,
// promedio, mejor nota, último examen), y tabs para alternar entre exámenes,
// resumen y detalle de intentos.
//
// Cada tab es un componente separado en ./componentes/ para mejor legibilidad.
// Los datos se cargan aquí y se pasan como props a cada tab.
//


import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useExamenesCurso } from '@/hooks/use-examenes-curso'
import api from '@/services/api'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { TabExamenesEstudiante } from './componentes/tab-examenes-estudiante'
import { TabResumenEstudiante } from './componentes/tab-resumen-estudiante'
import { TabIntentoEstudiante } from './componentes/tab-intento-estudiante'
import { TabLaboratoriosEstudiante } from './componentes/tab-laboratorios-estudiante'
import { TabCampoEstudioEstudiante } from './componentes/tab-campo-estudio-estudiante'
import {
  FileText,
  Loader2,
  BarChart3,
  Hash,
  Code2,
  Lightbulb,
} from 'lucide-react'
import type { MiConocimiento } from '@/types/analitica'

export default function PaginaExamenesCursoEstudiante() {
  const { id } = useParams<{ id: string }>()
  const { examenes, avance, estadoPorExamen, stats, cursoNombre, cargando, error } =
    useExamenesCurso(id)

  // Estado de conocimiento (analítica detallada).
  const [conocimiento, setConocimiento] = useState<MiConocimiento | null>(null)
  const [cargandoConocimiento, setCargandoConocimiento] = useState(true)

  // Carga el conocimiento del estudiante al montar el componente.
  useEffect(() => {
    if (!id) return

    const controlador = new AbortController()

    const cargarConocimiento = async () => {
      try {
        const { data } = await api.get<MiConocimiento>(
          `/analitica/mi-conocimiento/curso/${id}/`,
          { signal: controlador.signal }
        )
        setConocimiento(data)
      } catch {
        // Si falla la analítica, se muestra sin datos.
      } finally {
        if (!controlador.signal.aborted) {
          setCargandoConocimiento(false)
        }
      }
    }

    cargarConocimiento()
    return () => controlador.abort()
  }, [id])

  // Curso no encontrado en la URL.
  if (!id) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <FileText className="h-10 w-10 text-muted-foreground/50" />
        <p className="text-sm font-medium text-muted-foreground">
          Curso no encontrado
        </p>
        <Link
          to="/mis-cursos"
          className="text-sm text-primary hover:underline"
        >
          Volver a mis cursos
        </Link>
      </div>
    )
  }

  // Estado de carga: spinner centrado.
  if (cargando) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Estado de error.
  if (error) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <FileText className="h-10 w-10 text-muted-foreground/50" />
        <p className="text-sm font-medium text-muted-foreground">{error}</p>
        <Link
          to="/mis-cursos"
          className="text-sm text-primary hover:underline"
        >
          Volver a mis cursos
        </Link>
      </div>
    )
  }

  const nombreCurso = cursoNombre || 'Curso'

  return (
    <div className="space-y-6">
      {/* Header con gradiente del curso */}
      <EncabezadoGradiente
        titulo={nombreCurso}
        subtitulo="Exámenes disponibles para rendir"
        volverA="/mis-cursos"
        volverTexto="Volver a mis cursos"
        badgeTexto={
          stats.totalExamenes > 0
            ? `${stats.examenesRendidos} examenes rendidos`
            : undefined
        }
      />

      {/* Tabs de navegación */}
      <Tabs defaultValue="examenes">
        <TabsList>
          <TabsTrigger value="examenes">
            <FileText className="h-4 w-4" />
            Exámenes
          </TabsTrigger>
          <TabsTrigger value="resumen">
            <BarChart3 className="h-4 w-4" />
            Resumen
          </TabsTrigger>
          <TabsTrigger value="intentos">
            <Hash className="h-4 w-4" />
            Por examen
          </TabsTrigger>
          <TabsTrigger value="laboratorios">
            <Code2 className="h-4 w-4" />
            Laboratorios
          </TabsTrigger>
          <TabsTrigger value="campo-estudio">
            <Lightbulb className="h-4 w-4" />
            Campo de Estudio
          </TabsTrigger>
        </TabsList>

        {/* Tab de Exámenes */}
        <TabsContent value="examenes">
          <TabExamenesEstudiante
            examenes={examenes}
            estadoPorExamen={estadoPorExamen}
            cursoId={Number(id)}
          />
        </TabsContent>

        {/* Tab de Resumen */}
        <TabsContent value="resumen">
          {cargandoConocimiento ? (
            <div className="flex h-[40vh] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : conocimiento ? (
            <TabResumenEstudiante conocimiento={conocimiento} stats={stats} />
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
              <BarChart3 className="h-10 w-10 text-muted-foreground/50" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                No hay datos de conocimiento disponibles
              </p>
            </div>
          )}
        </TabsContent>

        {/* Tab de Por examen */}
        <TabsContent value="intentos">
          {avance && avance.resultados.length > 0 ? (
            <TabIntentoEstudiante resultados={avance.resultados} />
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
              <Hash className="h-10 w-10 text-muted-foreground/50" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                Aún no has rendido exámenes
              </p>
              <p className="text-xs text-muted-foreground">
                Los resultados aparecerán cuando rindas tu primer examen
              </p>
            </div>
          )}
        </TabsContent>

        {/* Tab de Laboratorios */}
        <TabsContent value="laboratorios">
          <TabLaboratoriosEstudiante cursoId={id} />
        </TabsContent>

        {/* Tab de Campo de Estudio */}
        <TabsContent value="campo-estudio">
          <TabCampoEstudioEstudiante cursoId={id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
