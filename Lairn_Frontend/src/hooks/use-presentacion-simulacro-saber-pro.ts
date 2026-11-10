// Hook de la presentación cronometrada de un simulacro Saber Pro (HU-21).
//
// Al montar inicia el intento con
// POST /saber-pro/estudiante/simulacros/{id}/presentaciones/. Expone las
// acciones de responder el bloque actual, finalizar manualmente, cerrar por
// salida y solicitar el desbloqueo remoto. Un intento finalizado nunca se
// reanuda: `salir` envía el intento al backend y lo deja cerrado. En cambio, un
// intento bloqueado sí se reanuda cuando el docente lo aprueba; si el docente lo
// rechaza, el sondeo detecta la finalización y la página muestra el resultado.
// Todas las respuestas del servidor son el estado completo, así que el hook
// reemplaza el objeto en vez de mutarlo.

import { useCallback, useEffect, useRef, useState } from 'react'
import api from '@/services/api'
import type {
  DatosRespuestaPresentacion,
  EstadoPresentacionSaberPro,
  MotivoSolicitudDesbloqueo,
} from '@/types/saber-pro'

interface ResultadoUsePresentacion {
  presentacion: EstadoPresentacionSaberPro | null
  cargando: boolean
  enviando: boolean
  error: string | null
  responder: (datos: DatosRespuestaPresentacion) => Promise<boolean>
  finalizar: () => Promise<boolean>
  salir: () => Promise<boolean>
  salirInminente: () => void
  solicitarDesbloqueo: (motivo: MotivoSolicitudDesbloqueo) => Promise<boolean>
  reintentar: () => void
}

function mensajeDeError(error: unknown): string {
  const axiosErr = error as {
    response?: { status?: number; data?: unknown }
  }
  const estado = axiosErr.response?.status
  // Durante un reinicio del backend nginx devuelve HTML 502/503/504; no lo
  // tratamos como un objeto de errores porque terminaría mostrando el HTML
  // carácter por carácter.
  if (estado === 502 || estado === 503 || estado === 504) {
    return 'El servicio no está disponible en este momento. Intenta de nuevo en unos segundos.'
  }

  const data = axiosErr.response?.data
  if (data && typeof data === 'object') {
    const registro = data as Record<string, unknown>
    if (typeof registro.detalle === 'string') return registro.detalle
    const mensajes = Object.values(registro)
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
  const saliendoRef = useRef(false)

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

  const presentacionId = presentacion?.presentacion_id ?? null
  const bloqueada = presentacion?.bloqueada ?? false
  const finalizada = presentacion?.finalizada ?? false

  // Mientras el intento está bloqueado, consulta el estado cada 4 s para
  // detectar la aprobación remota del docente y reanudar la pantalla.
  useEffect(() => {
    if (presentacionId === null || !bloqueada || finalizada) return

    const controlador = new AbortController()
    const consultar = () => {
      api
        .get<EstadoPresentacionSaberPro>(
          `/saber-pro/estudiante/presentaciones/${presentacionId}/`,
          { signal: controlador.signal }
        )
        .then(({ data }) => setPresentacion(data))
        .catch(() => undefined)
    }
    const intervalo = window.setInterval(consultar, 4000)
    return () => {
      window.clearInterval(intervalo)
      controlador.abort()
    }
  }, [bloqueada, finalizada, presentacionId])

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

  const salir = useCallback(async (): Promise<boolean> => {
    if (!presentacion) return false
    if (presentacion.finalizada) return true
    if (saliendoRef.current) return false

    saliendoRef.current = true
    try {
      const { data } = await api.post<EstadoPresentacionSaberPro>(
        `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/salir/`,
        {}
      )
      setPresentacion(data)
      return true
    } catch (err: unknown) {
      setError(mensajeDeError(err))
      return false
    } finally {
      saliendoRef.current = false
    }
  }, [presentacion])

  const solicitarDesbloqueo = useCallback(
    async (motivo: MotivoSolicitudDesbloqueo): Promise<boolean> => {
      if (!presentacion || presentacion.finalizada) return false
      if (presentacion.bloqueada) return true

      setEnviando(true)
      setError(null)
      try {
        const { data } = await api.post<EstadoPresentacionSaberPro>(
          `/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/solicitar-desbloqueo/`,
          { motivo }
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

  // Variante para `pagehide`: usa fetch con keepalive para que el envío alcance
  // al servidor incluso cuando el navegador está cerrando la página.
  const salirInminente = useCallback(() => {
    if (!presentacion || presentacion.finalizada) return

    const base = api.defaults.baseURL ?? ''
    const token = localStorage.getItem('access_token')
    void fetch(
      `${base}/saber-pro/estudiante/presentaciones/${presentacion.presentacion_id}/salir/`,
      {
        method: 'POST',
        keepalive: true,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: '{}',
      }
    ).catch(() => undefined)
  }, [presentacion])

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
    salir,
    salirInminente,
    solicitarDesbloqueo,
    reintentar,
  }
}
