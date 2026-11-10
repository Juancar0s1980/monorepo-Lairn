// Hook de la analítica de resultados de un curso Saber Pro (HU-24.1/24.2).
//
// Consulta GET /saber-pro/docente/cursos/{cursoId}/analitica/ con filtros
// opcionales de simulacro, periodo y criterio. El backend exige que el usuario
// sea el docente propietario del curso y devuelve resultados individuales y
// agregados. Los filtros se pasan como valores primitivos para que el efecto se
// recargue solo cuando cambia un criterio real (no en cada render).

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type {
  AnaliticaCursoSaberPro,
  ParametrosAnaliticaCursoSaberPro,
} from '@/types/saber-pro'

interface ResultadoUseAnaliticaCursoSaberPro {
  datos: AnaliticaCursoSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

function mensajeDeError(error: unknown): string {
  const axiosError = error as { response?: { data?: { detalle?: string } } }
  return axiosError.response?.data?.detalle ?? 'No se pudo cargar la analítica del curso.'
}

function paramsDeConsulta(parametros: ParametrosAnaliticaCursoSaberPro) {
  const { simulacro_id, periodo, competencia_id, afirmacion_id, parte } = parametros
  return {
    ...(simulacro_id === null ? {} : { simulacro_id }),
    ...(periodo ? { periodo } : {}),
    ...(competencia_id === null ? {} : { competencia_id }),
    ...(afirmacion_id === null ? {} : { afirmacion_id }),
    ...(parte === null ? {} : { parte }),
  }
}

export function useAnaliticaCursoSaberPro(
  cursoId: number | null,
  parametros: ParametrosAnaliticaCursoSaberPro
): ResultadoUseAnaliticaCursoSaberPro {
  const { simulacro_id, periodo, competencia_id, afirmacion_id, parte } = parametros
  const [datos, setDatos] = useState<AnaliticaCursoSaberPro | null>(null)
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<AnaliticaCursoSaberPro>(
        `/saber-pro/docente/cursos/${cursoId}/analitica/`,
        { params: paramsDeConsulta({ simulacro_id, periodo, competencia_id, afirmacion_id, parte }) }
      )
      setDatos(data)
      setError(null)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setCargando(false)
    }
    // `parametros` se desestructura arriba: las dependencias son sus valores.
  }, [cursoId, simulacro_id, periodo, competencia_id, afirmacion_id, parte])

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
        const { data } = await api.get<AnaliticaCursoSaberPro>(
          `/saber-pro/docente/cursos/${cursoId}/analitica/`,
          {
            params: paramsDeConsulta({ simulacro_id, periodo, competencia_id, afirmacion_id, parte }),
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
  }, [cursoId, simulacro_id, periodo, competencia_id, afirmacion_id, parte])

  return { datos, cargando, error, recargar }
}
