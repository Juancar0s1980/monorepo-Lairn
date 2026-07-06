// Hook personalizado para obtener y procesar todos los datos del dashboard del estudiante.
//
// Realiza las siguientes llamadas en paralelo:
//   1. GET /examenes/mis-cursos/ → lista de cursos
//   2. Para cada curso: GET /analitica/mi-avance/curso/{id}/ → avance y resultados
//   3. Para cada curso: GET /examenes/mis-cursos/{id}/examenes/ → exámenes disponibles
//
// Calcula métricas derivadas: stats globales, actividad reciente, rendimiento por concepto.

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { AvanceCurso } from '@/types/analitica'
import type { Examen } from '@/types/examen'

// Modelo de curso tal como lo devuelve el backend.
export interface Curso {
  id: number
  nombre: string
  docente: string
  descripcion: string
}

// Entrada de actividad reciente derivada de los resultados.
export interface ActividadReciente {
  cursoNombre: string
  cursoId: number
  examenId: number
  nota: number
  puntaje: number
  completadoEn: string
}

// Rendimiento agregado por concepto.
export interface RendimientoConcepto {
  concepto: string
  correctas: number
  total: number
  porcentaje: number
}

// Stats globales del estudiante.
export interface StatsEstudiante {
  totalCursos: number
  totalExamenes: number
  notaPromedio: number
  mejorNota: number
}

// Resultado del hook.
export interface DatosDashboard {
  cursos: Curso[]
  avances: Map<number, AvanceCurso>
  examenesPorCurso: Map<number, Examen[]>
  stats: StatsEstudiante
  actividadReciente: ActividadReciente[]
  rendimientoConceptos: RendimientoConcepto[]
  cargando: boolean
  error: string | null
}

// Valor inicial mientras carga.
const estadoInicial: DatosDashboard = {
  cursos: [],
  avances: new Map(),
  examenesPorCurso: new Map(),
  stats: { totalCursos: 0, totalExamenes: 0, notaPromedio: 0, mejorNota: 0 },
  actividadReciente: [],
  rendimientoConceptos: [],
  cargando: true,
  error: null,
}

export function useDashboardEstudiante(): DatosDashboard {
  const [datos, setDatos] = useState<DatosDashboard>(estadoInicial)

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    const cargarDatos = async () => {
      try {
        // 1. Obtener cursos del estudiante.
        const { data: cursos } = await api.get<Curso[]>('/examenes/mis-cursos/', {
          signal: controlador.signal,
        })

        if (!activo) return

        // 2. Para cada curso, obtener avance y exámenes en paralelo.
        const avances = new Map<number, AvanceCurso>()
        const examenesPorCurso = new Map<number, Examen[]>()

        const promesas = cursos.map(async (curso) => {
          const [resAvance, resExamenes] = await Promise.allSettled([
            api.get<AvanceCurso>(`/analitica/mi-avance/curso/${curso.id}/`, {
              signal: controlador.signal,
            }),
            api.get<Examen[]>(`/examenes/mis-cursos/${curso.id}/examenes/`, {
              signal: controlador.signal,
            }),
          ])

          if (resAvance.status === 'fulfilled') {
            avances.set(curso.id, resAvance.value.data)
          }
          if (resExamenes.status === 'fulfilled') {
            examenesPorCurso.set(curso.id, resExamenes.value.data)
          }
        })

        await Promise.allSettled(promesas)

        if (!activo) return

        // 3. Calcular stats globales.
        let totalExamenes = 0
        let sumaNotas = 0
        let mejorNota = 0

        for (const avance of avances.values()) {
          if (avance.total_examenes_presentados > 0) {
            totalExamenes += avance.total_examenes_presentados
            sumaNotas += avance.nota_promedio * avance.total_examenes_presentados
          }
          for (const resultado of avance.resultados) {
            if (resultado.nota > mejorNota) {
              mejorNota = resultado.nota
            }
          }
        }

        const notaPromedio = totalExamenes > 0 ? sumaNotas / totalExamenes : 0

        // 4. Construir actividad reciente (últimos 5 intentos globales).
        const todasActividades: ActividadReciente[] = []
        for (const avance of avances.values()) {
          for (const resultado of avance.resultados) {
            todasActividades.push({
              cursoNombre: avance.curso_nombre,
              cursoId: avance.curso_id,
              examenId: resultado.examen,
              nota: resultado.nota,
              puntaje: resultado.puntaje,
              completadoEn: resultado.completado_en,
            })
          }
        }
        todasActividades.sort(
          (a, b) => new Date(b.completadoEn).getTime() - new Date(a.completadoEn).getTime()
        )
        const actividadReciente = todasActividades.slice(0, 5)

        // 5. Agregar rendimiento por concepto desde todas las respuestas.
        const conceptosMap = new Map<string, { correctas: number; total: number }>()
        for (const avance of avances.values()) {
          for (const resultado of avance.resultados) {
            for (const resp of resultado.respuestas) {
              const actual = conceptosMap.get(resp.concepto) ?? { correctas: 0, total: 0 }
              const esCorrecta = !resp.respuesta_incorrecta
              conceptosMap.set(resp.concepto, {
                correctas: actual.correctas + (esCorrecta ? 1 : 0),
                total: actual.total + 1,
              })
            }
          }
        }

        const rendimientoConceptos = Array.from(conceptosMap.entries())
          .map(([concepto, datos]) => ({
            concepto: concepto.length > 30 ? concepto.slice(0, 30) + '…' : concepto,
            correctas: datos.correctas,
            total: datos.total,
            porcentaje: Math.round((datos.correctas / datos.total) * 100),
          }))
          .sort((a, b) => b.total - a.total)
          .slice(0, 8)

        if (activo) {
          setDatos({
            cursos,
            avances,
            examenesPorCurso,
            stats: {
              totalCursos: cursos.length,
              totalExamenes,
              notaPromedio,
              mejorNota,
            },
            actividadReciente,
            rendimientoConceptos,
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
