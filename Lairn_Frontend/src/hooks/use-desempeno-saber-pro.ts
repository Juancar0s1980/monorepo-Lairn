// Hook del desempeño propio del estudiante frente a su curso Saber Pro (HU-23).
//
// Consulta GET /saber-pro/estudiante/desempeno/ con `curso_id` y, cuando se
// elige, `simulacro_id`. La respuesta solo trae agregados propios y del grupo:
// nunca nombres, correos ni posiciones de otros estudiantes (HU-23.4).

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { DesempenoEstudianteSaberPro } from '@/types/saber-pro'

interface ResultadoUseDesempenoSaberPro {
  datos: DesempenoEstudianteSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

function mensajeDeError(error: unknown): string {
  const axiosError = error as { response?: { data?: { detalle?: string } } }
  return axiosError.response?.data?.detalle ?? 'No se pudo cargar tu desempeño.'
}

export function useDesempenoSaberPro(
  cursoId: number | null,
  simulacroId: number | null
): ResultadoUseDesempenoSaberPro {
  const [datos, setDatos] = useState<DesempenoEstudianteSaberPro | null>(null)
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<DesempenoEstudianteSaberPro>(
        '/saber-pro/estudiante/desempeno/',
        {
          params: {
            curso_id: cursoId,
            ...(simulacroId === null ? {} : { simulacro_id: simulacroId }),
          },
        }
      )
      setDatos(data)
      setError(null)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setCargando(false)
    }
  }, [cursoId, simulacroId])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (cursoId === null) {
        setDatos(null)
        setCargando(false)
        setError(null)
        return
      }

      setCargando(true)
      try {
        const { data } = await api.get<DesempenoEstudianteSaberPro>(
          '/saber-pro/estudiante/desempeno/',
          {
            params: {
              curso_id: cursoId,
              ...(simulacroId === null ? {} : { simulacro_id: simulacroId }),
            },
            signal: controlador.signal,
          }
        )
        if (activo) {
          setDatos(data)
          setError(null)
        }
      } catch (err) {
        if (activo) setError(mensajeDeError(err))
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId, simulacroId])

  return { datos, cargando, error, recargar }
}
