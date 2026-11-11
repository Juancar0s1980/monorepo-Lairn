// Hook de las opciones de filtro de "Mi desempeño" del estudiante Saber Pro (HU-23).
//
// Llama a GET /saber-pro/estudiante/desempeno/opciones/: los cursos inscritos
// donde el estudiante tiene resultados calificados y, por curso, los
// simulacros que presentó. Con esto los filtros de la página nunca ofrecen
// simulacros sin resultados propios.

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { OpcionCursoDesempenoSaberPro } from '@/types/saber-pro'

interface ResultadoUseOpcionesDesempenoSaberPro {
  opciones: OpcionCursoDesempenoSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useOpcionesDesempenoSaberPro(): ResultadoUseOpcionesDesempenoSaberPro {
  const [opciones, setOpciones] = useState<OpcionCursoDesempenoSaberPro[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<OpcionCursoDesempenoSaberPro[]>(
        '/saber-pro/estudiante/desempeno/opciones/'
      )
      setOpciones(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar tus resultados para comparar.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      try {
        const { data } = await api.get<OpcionCursoDesempenoSaberPro[]>(
          '/saber-pro/estudiante/desempeno/opciones/',
          { signal: controlador.signal }
        )
        if (activo) {
          setOpciones(data)
          setError(null)
        }
      } catch (err) {
        if (activo && (err as { name?: string }).name !== 'CanceledError') {
          setError('No se pudieron cargar tus resultados para comparar.')
        }
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

  return { opciones, cargando, error, recargar }
}
