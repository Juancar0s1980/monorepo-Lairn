// Hook personalizado para obtener y procesar todos los datos del dashboard del docente.
//
// Realiza las siguientes llamadas en paralelo:
//   1. GET /examenes/cursos/ → lista de cursos del docente
//   2. GET /examenes/examenes/ → todos los exámenes (filtrar por curso)
//   3. Para cada curso: GET /analitica/curso/{id}/resumen/ → estudiantes y promedio
//
// Calcula métricas derivadas: stats globales, cursos con datos de estudiantes.

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { Examen } from '@/types/examen'
import type { ResumenCursoDocente } from '@/types/analitica'

// Modelo de curso con stats calculadas.
export interface CursoConStats {
  id: number
  nombre: string
  codigo: string
  descripcion: string
  totalInscritos: number
  notaPromedio: number | undefined
  totalExamenes: number
  tasaAprobados: number | undefined
}

// Stats globales del docente.
export interface StatsDocente {
  totalCursos: number
  totalExamenes: number
  totalEstudiantes: number
  promedioGeneral: number
}

// Resultado del hook.
export interface DatosDashboardDocente {
  cursos: CursoConStats[]
  stats: StatsDocente
  cargando: boolean
  error: string | null
}

// Valor inicial mientras carga.
const estadoInicial: DatosDashboardDocente = {
  cursos: [],
  stats: { totalCursos: 0, totalExamenes: 0, totalEstudiantes: 0, promedioGeneral: 0 },
  cargando: true,
  error: null,
}

export function useDashboardDocente(): DatosDashboardDocente {
  const [datos, setDatos] = useState<DatosDashboardDocente>(estadoInicial)

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    const cargarDatos = async () => {
      try {
        // 1. Obtener cursos y exámenes en paralelo.
        const [resCursos, resExamenes] = await Promise.all([
          api.get<Array<{ id: number; nombre: string; codigo: string; descripcion: string }>>(
            '/examenes/cursos/',
            { signal: controlador.signal }
          ),
          api.get<Examen[]>('/examenes/examenes/', {
            signal: controlador.signal,
          }),
        ])

        if (!activo) return

        const cursosRaw = resCursos.data
        const todosExamenes = resExamenes.data

        // 2. Para cada curso, obtener el resumen de analítica.
        const resumenes = new Map<number, ResumenCursoDocente>()

        const promesas = cursosRaw.map(async (curso) => {
          try {
            const { data } = await api.get<ResumenCursoDocente>(
              `/analitica/curso/${curso.id}/resumen/`,
              { signal: controlador.signal }
            )
            resumenes.set(curso.id, data)
          } catch {
            // Si falla un curso individual, continuamos con los demás.
          }
        })

        await Promise.allSettled(promesas)

        if (!activo) return

        // 3. Construir cursos con stats.
        const cursos: CursoConStats[] = cursosRaw.map((curso) => {
          const resumen = resumenes.get(curso.id)
          const examenesDelCurso = todosExamenes.filter(
            (e) => e.curso === curso.id
          )

          return {
            id: curso.id,
            nombre: curso.nombre,
            codigo: curso.codigo,
            descripcion: curso.descripcion,
            totalInscritos: resumen?.total_inscritos ?? 0,
            notaPromedio: resumen?.nota_promedio_curso,
            totalExamenes: examenesDelCurso.length,
            tasaAprobados: undefined, // El endpoint de resumen no trae tasa de aprobados
          }
        })

        // 4. Calcular stats globales.
        const totalEstudiantes = cursos.reduce(
          (acc, c) => acc + c.totalInscritos,
          0
        )
        const cursosConPromedio = cursos.filter((c) => c.notaPromedio !== undefined && c.notaPromedio > 0)
        const promedioGeneral =
          cursosConPromedio.length > 0
            ? cursosConPromedio.reduce((acc, c) => acc + (c.notaPromedio ?? 0), 0) /
              cursosConPromedio.length
            : 0

        if (activo) {
          setDatos({
            cursos,
            stats: {
              totalCursos: cursos.length,
              totalExamenes: todosExamenes.length,
              totalEstudiantes,
              promedioGeneral,
            },
            cargando: false,
            error: null,
          })
        }
      } catch (err: unknown) {
        if (!activo || controlador.signal.aborted) return
        const mensaje =
          err instanceof Error ? err.message : 'Error al cargar el dashboard'
        setDatos({ ...estadoInicial, cargando: false, error: mensaje })
      }
    }

    cargarDatos()

    return () => {
      activo = false
      controlador.abort()
    }
  }, [])

  return datos
}
