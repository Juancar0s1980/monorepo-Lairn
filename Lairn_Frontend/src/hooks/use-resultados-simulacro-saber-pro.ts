// Hook de calificaciones de un simulacro Saber Pro para el docente.
//
// Consulta GET /saber-pro/docente/cursos/{cursoId}/simulacros/{simulacroId}/resultados/
// solo cuando el docente abre el modal. La respuesta incluye los intentos
// finalizados con calificación 0.0-5.0 y un resumen agregado del grupo.

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { ResultadosSimulacroSaberPro } from '@/types/saber-pro'

interface ResultadoUseResultadosSimulacro {
  datos: ResultadosSimulacroSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useResultadosSimulacroSaberPro(
  cursoId: number | null,
  simulacroId: number | null,
  habilitado: boolean
): ResultadoUseResultadosSimulacro {
  const [datos, setDatos] = useState<ResultadosSimulacroSaberPro | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (!habilitado || cursoId === null || simulacroId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<ResultadosSimulacroSaberPro>(
        `/saber-pro/docente/cursos/${cursoId}/simulacros/${simulacroId}/resultados/`
      )
      setDatos(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar las calificaciones del simulacro.')
    } finally {
      setCargando(false)
    }
  }, [cursoId, habilitado, simulacroId])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (!habilitado || cursoId === null || simulacroId === null) {
        setDatos(null)
        setCargando(false)
        setError(null)
        return
      }
      setCargando(true)
      try {
        const { data } = await api.get<ResultadosSimulacroSaberPro>(
          `/saber-pro/docente/cursos/${cursoId}/simulacros/${simulacroId}/resultados/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setDatos(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudieron cargar las calificaciones del simulacro.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId, habilitado, simulacroId])

  return { datos, cargando, error, recargar }
}
