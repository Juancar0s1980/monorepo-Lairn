// Hook de la analítica académica institucional de Saber Pro (HU-24.3/24.4).
//
// Consulta GET /saber-pro/institucional/analitica/ con filtros opcionales de
// curso, carrera, área, criterio y periodo. La respuesta es consolidada: no
// incluye resultados individuales. El permiso lo impone el backend
// (`EsLectorAnalitica`: Coordinador, Vicerrector y Administrador en lectura).

import { useCallback, useEffect, useState } from 'react'
import api from '@/services/api'
import type {
  AnaliticaInstitucionalSaberPro,
  ParametrosAnaliticaInstitucionalSaberPro,
} from '@/types/saber-pro'

interface ResultadoUseAnaliticaInstitucionalSaberPro {
  datos: AnaliticaInstitucionalSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

function mensajeDeError(error: unknown): string {
  const axiosError = error as { response?: { data?: { detalle?: string } } }
  return (
    axiosError.response?.data?.detalle ??
    'No se pudo cargar la analítica institucional de Saber Pro.'
  )
}

function paramsDeConsulta(parametros: ParametrosAnaliticaInstitucionalSaberPro) {
  const { curso_id, programa_id, area_id, competencia_id, afirmacion_id, parte, periodo } = parametros
  return {
    ...(curso_id === null ? {} : { curso_id }),
    ...(programa_id === null ? {} : { programa_id }),
    ...(area_id === null ? {} : { area_id }),
    ...(competencia_id === null ? {} : { competencia_id }),
    ...(afirmacion_id === null ? {} : { afirmacion_id }),
    ...(parte === null ? {} : { parte }),
    ...(periodo ? { periodo } : {}),
  }
}

export function useAnaliticaInstitucionalSaberPro(
  parametros: ParametrosAnaliticaInstitucionalSaberPro
): ResultadoUseAnaliticaInstitucionalSaberPro {
  const { curso_id, programa_id, area_id, competencia_id, afirmacion_id, parte, periodo } = parametros
  const [datos, setDatos] = useState<AnaliticaInstitucionalSaberPro | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<AnaliticaInstitucionalSaberPro>(
        '/saber-pro/institucional/analitica/',
        {
          params: paramsDeConsulta({
            curso_id,
            programa_id,
            area_id,
            competencia_id,
            afirmacion_id,
            parte,
            periodo,
          }),
        }
      )
      setDatos(data)
      setError(null)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setCargando(false)
    }
    // `parametros` se desestructura arriba: las dependencias son sus valores.
  }, [curso_id, programa_id, area_id, competencia_id, afirmacion_id, parte, periodo])

  useEffect(() => {
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      setCargando(true)
      try {
        const { data } = await api.get<AnaliticaInstitucionalSaberPro>(
          '/saber-pro/institucional/analitica/',
          {
            params: paramsDeConsulta({
              curso_id,
              programa_id,
              area_id,
              competencia_id,
              afirmacion_id,
              parte,
              periodo,
            }),
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
  }, [curso_id, programa_id, area_id, competencia_id, afirmacion_id, parte, periodo])

  return { datos, cargando, error, recargar }
}
