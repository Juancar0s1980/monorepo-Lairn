// Hook con el banco aprobado disponible para configurar un simulacro (HU-19.2).
//
// Llama a GET /saber-pro/docente/cursos/{id}/simulacros/disponibilidad/ cuando
// el modal se abre. Permite mostrar cuantas preguntas aprobadas hay por
// competencia, afirmacion o parte de Ingles antes de guardar la distribucion.

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { DisponibilidadSimulacroSaberPro } from '@/types/saber-pro'

interface ResultadoUseDisponibilidad {
  disponibilidad: DisponibilidadSimulacroSaberPro | null
  cargando: boolean
  error: string | null
}

export function useDisponibilidadSimulacroSaberPro(
  cursoId: number | null,
  habilitado: boolean
): ResultadoUseDisponibilidad {
  const [disponibilidad, setDisponibilidad] = useState<DisponibilidadSimulacroSaberPro | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (!habilitado || cursoId === null) {
        setDisponibilidad(null)
        setCargando(false)
        setError(null)
        return
      }
      setCargando(true)
      try {
        const { data } = await api.get<DisponibilidadSimulacroSaberPro>(
          `/saber-pro/docente/cursos/${cursoId}/simulacros/disponibilidad/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setDisponibilidad(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudo consultar el contenido aprobado del area.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId, habilitado])

  return { disponibilidad, cargando, error }
}
