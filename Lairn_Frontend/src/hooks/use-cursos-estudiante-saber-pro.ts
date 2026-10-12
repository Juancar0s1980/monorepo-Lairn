// Hook para listar los cursos Saber Pro a los que el estudiante se ha unido (HU-18.3).
//
// Llama a GET /saber-pro/estudiante/cursos/, que parte de las inscripciones del
// estudiante autenticado (la fuente de verdad de la relación estudiante-curso).
// Expone `recargar()` para refrescar la lista tras unirse con un código nuevo,
// mismo patrón que `use-cursos-saber-pro` del docente (HU-17).

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { InscripcionCursoSaberPro } from '@/types/saber-pro'

interface ResultadoUseCursosEstudianteSaberPro {
  inscripciones: InscripcionCursoSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useCursosEstudianteSaberPro(): ResultadoUseCursosEstudianteSaberPro {
  const [inscripciones, setInscripciones] = useState<InscripcionCursoSaberPro[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Recarga la lista desde el backend (se usa tras unirse a un curso con código).
  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<InscripcionCursoSaberPro[]>('/saber-pro/estudiante/cursos/')
      setInscripciones(data)
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
        const { data } = await api.get<InscripcionCursoSaberPro[]>('/saber-pro/estudiante/cursos/')
        if (activo) setInscripciones(data)
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

  return { inscripciones, cargando, error, recargar }
}