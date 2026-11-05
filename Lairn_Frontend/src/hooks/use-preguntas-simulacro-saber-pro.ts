// Hook de consulta de las preguntas asignadas a un simulacro Saber Pro (HU-19.4).
//
// Llama a GET /saber-pro/docente/cursos/{cursoId}/simulacros/{simulacroId}/preguntas/
// solo cuando el docente abre la vista de solo lectura. La respuesta incluye el
// contenido completo de cada pregunta, con su respuesta correcta y su orden.

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { PreguntasSimulacroSaberPro } from '@/types/saber-pro'

interface ResultadoUsePreguntasSimulacro {
  datos: PreguntasSimulacroSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function usePreguntasSimulacroSaberPro(
  cursoId: number | null,
  simulacroId: number | null,
  habilitado: boolean
): ResultadoUsePreguntasSimulacro {
  const [datos, setDatos] = useState<PreguntasSimulacroSaberPro | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (!habilitado || cursoId === null || simulacroId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<PreguntasSimulacroSaberPro>(
        `/saber-pro/docente/cursos/${cursoId}/simulacros/${simulacroId}/preguntas/`
      )
      setDatos(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar las preguntas asignadas al simulacro.')
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
        const { data } = await api.get<PreguntasSimulacroSaberPro>(
          `/saber-pro/docente/cursos/${cursoId}/simulacros/${simulacroId}/preguntas/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setDatos(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudieron cargar las preguntas asignadas al simulacro.')
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
