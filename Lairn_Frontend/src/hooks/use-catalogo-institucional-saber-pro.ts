// Hook del catálogo de filtros de la analítica institucional Saber Pro (HU-24.3).
//
// Consulta GET /saber-pro/institucional/catalogo/ (áreas, carreras y cursos).
// Se usa para poblar los selectores de la vista institucional sin depender de
// endpoints restringidos al docente o al gestor académico.

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { CatalogoInstitucionalSaberPro } from '@/types/saber-pro'

interface ResultadoUseCatalogoInstitucionalSaberPro {
  catalogo: CatalogoInstitucionalSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useCatalogoInstitucionalSaberPro(): ResultadoUseCatalogoInstitucionalSaberPro {
  const [catalogo, setCatalogo] = useState<CatalogoInstitucionalSaberPro | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<CatalogoInstitucionalSaberPro>(
        '/saber-pro/institucional/catalogo/'
      )
      setCatalogo(data)
      setError(null)
    } catch {
      setError('No se pudo cargar el catálogo de áreas, carreras y cursos.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    let activo = true

    async function cargar() {
      try {
        const { data } = await api.get<CatalogoInstitucionalSaberPro>(
          '/saber-pro/institucional/catalogo/'
        )
        if (activo) {
          setCatalogo(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudo cargar el catálogo de áreas, carreras y cursos.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
    }
  }, [])

  return { catalogo, cargando, error, recargar }
}
