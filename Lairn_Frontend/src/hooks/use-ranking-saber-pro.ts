// Hook del ranking nominal de un curso Saber Pro para el docente (HU-23).
//
// Consulta GET /saber-pro/docente/cursos/{cursoId}/ranking/ y acepta el filtro
// opcional `simulacro_id`. Sin simulacro compara todo el curso (área): el
// backend promedia el mejor intento de cada simulacro por estudiante.

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type { RankingCursoSaberPro } from '@/types/saber-pro'

interface ResultadoUseRankingSaberPro {
  datos: RankingCursoSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

function mensajeDeError(error: unknown): string {
  const axiosError = error as { response?: { data?: { detalle?: string } } }
  return axiosError.response?.data?.detalle ?? 'No se pudo cargar el ranking del curso.'
}

export function useRankingSaberPro(
  cursoId: number | null,
  simulacroId: number | null
): ResultadoUseRankingSaberPro {
  const [datos, setDatos] = useState<RankingCursoSaberPro | null>(null)
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<RankingCursoSaberPro>(
        `/saber-pro/docente/cursos/${cursoId}/ranking/`,
        { params: simulacroId === null ? {} : { simulacro_id: simulacroId } }
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
        const { data } = await api.get<RankingCursoSaberPro>(
          `/saber-pro/docente/cursos/${cursoId}/ranking/`,
          {
            params: simulacroId === null ? {} : { simulacro_id: simulacroId },
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
