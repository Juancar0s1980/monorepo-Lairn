// Hook para listar los simulacros de un curso Saber Pro del docente (HU-19).
//
// Llama a GET /saber-pro/docente/cursos/{id}/simulacros/ y expone `recargar()`
// para refrescar la lista despues de crear, editar o eliminar un simulacro.

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { SimulacroSaberPro } from '@/types/saber-pro'

interface ResultadoUseSimulacrosSaberPro {
  simulacros: SimulacroSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useSimulacrosSaberPro(cursoId: number | null): ResultadoUseSimulacrosSaberPro {
  const [simulacros, setSimulacros] = useState<SimulacroSaberPro[]>([])
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<SimulacroSaberPro[]>(
        `/saber-pro/docente/cursos/${cursoId}/simulacros/`
      )
      setSimulacros(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar los simulacros del curso.')
    } finally {
      setCargando(false)
    }
  }, [cursoId])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (cursoId === null) {
        setSimulacros([])
        setCargando(false)
        setError(null)
        return
      }
      setCargando(true)
      try {
        const { data } = await api.get<SimulacroSaberPro[]>(
          `/saber-pro/docente/cursos/${cursoId}/simulacros/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setSimulacros(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudieron cargar los simulacros del curso.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId])

  return { simulacros, cargando, error, recargar }
}
