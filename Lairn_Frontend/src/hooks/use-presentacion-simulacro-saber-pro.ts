// Hook de la presentación cronometrada de un simulacro Saber Pro (HU-21).
//
// Al montar inicia o reanuda el intento con
// POST /saber-pro/estudiante/simulacros/{id}/presentaciones/. Expone las
// acciones de responder el bloque actual y finalizar manualmente. Todas las
// respuestas del servidor son el estado completo, así que el hook reemplaza el
// objeto en vez de mutarlo.

import { useCallback, useEffect, useRef, useState } from 'react'
import api from '@/services/api'
import type {
  DatosRespuestaPresentacion,
  EstadoPresentacionSaberPro,
} from '@/types/saber-pro'

interface ResultadoDesbloqueo {
  ok: boolean
  error?: string
}

interface ResultadoUsePresentacion {
  presentacion: EstadoPresentacionSaberPro | null
  cargando: boolean
  enviando: boolean
  error: string | null
  responder: (datos: DatosRespuestaPresentacion) => Promise<boolean>
  finalizar: () => Promise<boolean>
  bloquear: () => Promise<boolean>
  desbloquear: (codigo: string) => Promise<ResultadoDesbloqueo>
  reintentar: () => void
}

function mensajeDeError(error: unknown): string {
  const axiosErr = error as {
    response?: { data?: Record<string, unknown> }
  }
  const data = axiosErr.response?.data
  if (data) {
    if (typeof data.detalle === 'string') return data.detalle
    const mensajes = Object.values(data)
      .flatMap((valor) => (Array.isArray(valor) ? valor : [valor]))
      .filter((valor): valor is string => typeof valor === 'string')
    if (mensajes.length > 0) return mensajes.join('. ')
  }
  return 'No se pudo completar la operación con el simulacro.'
}

export function usePresentacionSimulacroSaberPro(
  simulacroId: number | null
): ResultadoUsePresentacion {
  const [presentacion, setPresentacion] = useState<EstadoPresentacionSaberPro | null>(null)
  const [cargando, setCargando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [intentoInicio, setIntentoInicio] = useState(0)
  const bloqueandoRef = useRef(false)

  useEffect(() => {
    if (simulacroId === null) return

    const controlador = new AbortController()

    api
      .post<EstadoPresentacionSaberPro>(
        `/saber-pro/estudiante/simulacros/${simulacroId}/presentaciones/`,
        {},
        { signal: controlador.signal }
      )
      .then(({ data }) => setPresentacion(data))
      .catch((err: unknown) => {
        if (!controlador.signal.aborted) setError(mensajeDeError(err))
      })
      .finally(() => {
        if (!controlador.signal.aborted) setCargando(false)
      })

    return () => controlador.abort()
  }, [simulacroId, intentoInicio])

  const responder = useCallback(
    async (datos: DatosRespuestaPresentacion): Promise<boolean> => {
      if (!presentacion) return false
      setEnviando(true)
      setError(null)
      try {
        const { data } = await api.post<EstadoPresentacionSaberPro>(
          `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/responder/`,
          datos
        )
        setPresentacion(data)
        return true
      } catch (err: unknown) {
        setError(mensajeDeError(err))
        return false
      } finally {
        setEnviando(false)
      }
    },
    [presentacion]
  )

  const finalizar = useCallback(async (): Promise<boolean> => {
    if (!presentacion) return false
    setEnviando(true)
    setError(null)
    try {
      const { data } = await api.post<EstadoPresentacionSaberPro>(
        `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/finalizar/`,
        {}
      )
      setPresentacion(data)
      return true
    } catch (err: unknown) {
      setError(mensajeDeError(err))
      return false
    } finally {
      setEnviando(false)
    }
  }, [presentacion])

  const bloquear = useCallback(async (): Promise<boolean> => {
    if (!presentacion || presentacion.finalizada || presentacion.bloqueada) return false
    if (bloqueandoRef.current) return false

    bloqueandoRef.current = true
    try {
      const { data } = await api.post<EstadoPresentacionSaberPro>(
        `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/bloquear/`,
        {}
      )
      setPresentacion(data)
      return true
    } catch {
      return false
    } finally {
      bloqueandoRef.current = false
    }
  }, [presentacion])

  const desbloquear = useCallback(
    async (codigo: string): Promise<ResultadoDesbloqueo> => {
      if (!presentacion) {
        return { ok: false, error: 'No hay una presentación activa para desbloquear.' }
      }

      setEnviando(true)
      setError(null)
      try {
        const { data } = await api.post<EstadoPresentacionSaberPro>(
          `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/desbloquear/`,
          { codigo }
        )
        setPresentacion(data)
        return { ok: true }
      } catch (err: unknown) {
        const mensaje = mensajeDeError(err)
        setError(mensaje)
        return { ok: false, error: mensaje }
      } finally {
        setEnviando(false)
      }
    },
    [presentacion]
  )

  const reintentar = useCallback(() => {
    setCargando(true)
    setError(null)
    setIntentoInicio((valor) => valor + 1)
  }, [])

  return {
    presentacion,
    cargando,
    enviando,
    error,
    responder,
    finalizar,
    bloquear,
    desbloquear,
    reintentar,
  }
}
