// Hook para listar y gestionar los cursos Saber Pro del docente (HU-17).
//
// Expone la lista de cursos del docente autenticado (`GET /saber-pro/docente/cursos/`)
// y un `recargar()` para refrescarla después de las mutaciones (crear, editar,
// regenerar código, eliminar). Las mutaciones en sí las ejecutan los componentes
// llamando a la API directamente (mismo patrón que los cursos de exámenes), y luego
// invocan `recargar()` para reflejar el cambio en la lista.

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { CursoSaberPro } from '@/types/saber-pro'

interface ResultadoUseCursosSaberPro {
  cursos: CursoSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useCursosSaberPro(): ResultadoUseCursosSaberPro {
  const [cursos, setCursos] = useState<CursoSaberPro[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Recarga la lista desde el backend (se usa tras crear/editar/eliminar un curso).
  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<CursoSaberPro[]>('/saber-pro/docente/cursos/')
      setCursos(data)
      setError(null)
    } catch {
      setError('No se pudieron cargar tus cursos Saber Pro.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    let activo = true

    async function cargar() {
      try {
        const { data } = await api.get<CursoSaberPro[]>('/saber-pro/docente/cursos/')
        if (activo) setCursos(data)
      } catch {
        if (activo) setError('No se pudieron cargar tus cursos Saber Pro.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
    }
  }, [])

  return { cursos, cargando, error, recargar }
}