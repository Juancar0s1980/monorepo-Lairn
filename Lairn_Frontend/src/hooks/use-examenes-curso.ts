// Hook personalizado para obtener exámenes y analítica de un curso específico.
//
// Realiza las siguientes llamadas en paralelo:
//   1. GET /examenes/mis-cursos/{cursoId}/examenes/ → exámenes disponibles
//   2. GET /analitica/mi-avance/curso/{cursoId}/ → avance y resultados previos
//
// Calcula métricas derivadas: stats del curso, estado de intentos por examen.

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { AvanceCurso, Resultado } from '@/types/analitica'
import type { Examen } from '@/types/examen'

// Estado de intentos de un examen específico.
export interface EstadoExamen {
  ultimaNota?: number
  intentosUsados: number
  aprobado: boolean
}

// Stats globales del curso para el estudiante.
export interface StatsCurso {
  examenesRendidos: number
  totalExamenes: number
  notaPromedio: number
  mejorNota: number
  ultimoExamenEn: string | null
}

// Resultado del hook.
export interface DatosExamenCurso {
  examenes: Examen[]
  avance: AvanceCurso | null
  estadoPorExamen: Map<number, EstadoExamen>
  stats: StatsCurso
  cursoNombre: string
  cargando: boolean
  error: string | null
}

// Valor inicial mientras carga.
const estadoInicial: DatosExamenCurso = {
  examenes: [],
  avance: null,
  estadoPorExamen: new Map(),
  stats: {
    examenesRendidos: 0,
    totalExamenes: 0,
    notaPromedio: 0,
    mejorNota: 0,
    ultimoExamenEn: null,
  },
  cursoNombre: '',
  cargando: true,
  error: null,
}

export function useExamenesCurso(cursoId: string | undefined): DatosExamenCurso {
  const [datos, setDatos] = useState<DatosExamenCurso>(estadoInicial)

  useEffect(() => {
    if (!cursoId) {
      // El componente debe mostrar error cuando error !== null && cargando === false.
      // No llamamos setState aquí para evitar cascada de renders.
      return
    }

    const controlador = new AbortController()
    let activo = true

    const cargarDatos = async () => {
      try {
        // Obtener exámenes y avance en paralelo.
        const [resExamenes, resAvance] = await Promise.allSettled([
          api.get<Examen[]>(`/examenes/mis-cursos/${cursoId}/examenes/`, {
            signal: controlador.signal,
          }),
          api.get<AvanceCurso>(`/analitica/mi-avance/curso/${cursoId}/`, {
            signal: controlador.signal,
          }),
        ])

        if (!activo) return

        const examenes =
          resExamenes.status === 'fulfilled' ? resExamenes.value.data : []
        const avance =
          resAvance.status === 'fulfilled' ? resAvance.value.data : null

        // Construir estado por examen: agrupar resultados por examen_id.
        const estadoPorExamen = new Map<number, EstadoExamen>()
        if (avance) {
          // Agrupar resultados por examen.
          const resultadosPorExamen = new Map<number, Resultado[]>()
          for (const resultado of avance.resultados) {
            const lista = resultadosPorExamen.get(resultado.examen) ?? []
            lista.push(resultado)
            resultadosPorExamen.set(resultado.examen, lista)
          }

          for (const [examenId, resultados] of resultadosPorExamen) {
            // Ordenar por fecha descendente para obtener el más reciente.
            resultados.sort(
              (a, b) =>
                new Date(b.completado_en).getTime() -
                new Date(a.completado_en).getTime()
            )
            const ultimo = resultados[0]
            estadoPorExamen.set(examenId, {
              ultimaNota: ultimo.nota,
              intentosUsados: resultados.length,
              aprobado: ultimo.nota >= 3.0,
            })
          }
        }

        // Calcular stats globales del curso.
        let notaPromedio = 0
        let mejorNota = 0
        let ultimoExamenEn: string | null = null

        if (avance && avance.total_examenes_presentados > 0) {
          notaPromedio = avance.nota_promedio

          for (const resultado of avance.resultados) {
            if (resultado.nota > mejorNota) {
              mejorNota = resultado.nota
            }
            if (
              !ultimoExamenEn ||
              new Date(resultado.completado_en).getTime() >
                new Date(ultimoExamenEn).getTime()
            ) {
              ultimoExamenEn = resultado.completado_en
            }
          }
        }

        if (activo) {
          setDatos({
            examenes,
            avance,
            estadoPorExamen,
            stats: {
              examenesRendidos: avance?.total_examenes_presentados ?? 0,
              totalExamenes: examenes.length,
              notaPromedio,
              mejorNota,
              ultimoExamenEn,
            },
            cursoNombre: avance?.curso_nombre ?? '',
            cargando: false,
            error: null,
          })
        }
      } catch (err: unknown) {
        if (!activo || controlador.signal.aborted) return
        const mensaje =
          err instanceof Error ? err.message : 'Error al cargar los exámenes'
        setDatos({ ...estadoInicial, cargando: false, error: mensaje })
      }
    }

    cargarDatos()

    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId])

  return datos
}
