// Hook para listar los simulacros activos del estudiante inscrito (HU-19.5).
//
// Llama a GET /saber-pro/estudiante/simulacros/; el backend solo devuelve
// simulacros activos de cursos activos a los que el estudiante pertenece.

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { SimulacroEstudianteSaberPro } from '@/types/saber-pro'

interface ResultadoUseSimulacrosEstudiante {
  simulacros: SimulacroEstudianteSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useSimulacrosEstudianteSaberPro(): ResultadoUseSimulacrosEstudiante {
  const [simulacros, setSimulacros] = useState<SimulacroEstudianteSaberPro[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<SimulacroEstudianteSaberPro[]>(
        '/saber-pro/estudiante/simulacros/'
      )
      setSimulacros(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar tus simulacros disponibles.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      try {
        const { data } = await api.get<SimulacroEstudianteSaberPro[]>(
          '/saber-pro/estudiante/simulacros/',
          { signal: controlador.signal }
        )
        if (activo) {
          setSimulacros(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudieron cargar tus simulacros disponibles.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [])

  return { simulacros, cargando, error, recargar }
}
