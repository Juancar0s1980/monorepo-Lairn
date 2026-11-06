// Integridad académica durante un intento en curso (ADR-010).
//
// El navegador NO puede impedir que el estudiante cambie de pestaña o de
// ventana: lo que hace este hook es BLOQUEAR copiar/cortar/pegar, menú
// contextual, arrastrar, seleccionar y los atajos Ctrl/Cmd + C, X, V, A, P, S, U,
// y DETECTAR cambio de pestaña o ventana y salida de pantalla completa.
// Cada incidente se reporta al servidor, que decide advertencia o suspensión.
// Eventos casi simultáneos (blur + visibilitychange) se agrupan en uno (2 s).

import { useCallback, useEffect, useRef } from 'react'
import api from '@/services/api'

export type TipoIncidente =
  | 'copiar'
  | 'cortar'
  | 'pegar'
  | 'menu_contextual'
  | 'cambio_pestana'
  | 'salir_pantalla_completa'
  | 'pantalla_completa_no_disponible'

export interface RespuestaIncidente {
  consecuencia: 'advertencia' | 'suspension' | 'agrupado' | 'sin_efecto'
  integridad: string
  aviso: string | null
}

const VENTANA_AGRUPACION_MS = 2000
// Al pedir pantalla completa el navegador puede disparar blur: no es un incidente.
const GRACIA_PANTALLA_COMPLETA_MS = 1500
const ATAJOS: Record<string, TipoIncidente | null> = { c: 'copiar', x: 'cortar', v: 'pegar', a: null, p: null, s: null, u: null }

// Pide pantalla completa (debe llamarse dentro de un clic). Devuelve si se logró.
// Algunos navegadores nunca resuelven la promesa (p. ej. vistas embebidas):
// se espera como máximo 1,5 s y se sigue sin pantalla completa, sin bloquear.
const ESPERA_PANTALLA_COMPLETA_MS = 1500
export async function pedirPantallaCompleta(): Promise<boolean> {
  if (document.fullscreenElement) return true
  if (!document.documentElement.requestFullscreen) return false
  const pedido = document.documentElement.requestFullscreen().then(
    () => true,
    () => false,
  )
  const limite = new Promise<boolean>((resolver) => window.setTimeout(() => resolver(false), ESPERA_PANTALLA_COMPLETA_MS))
  const logrado = await Promise.race([pedido, limite])
  return logrado || !!document.fullscreenElement
}

export function useIntegridad({
  evaluacionId,
  activo,
  alResponder,
}: {
  evaluacionId: string
  activo: boolean
  alResponder: (r: RespuestaIncidente) => void
}) {
  const ultimo = useRef(0)
  const ignorarHasta = useRef(0)
  const alResponderRef = useRef(alResponder)
  useEffect(() => {
    alResponderRef.current = alResponder
  })

  const reportar = useCallback(
    async (tipo: TipoIncidente, detalle = '') => {
      const ahora = Date.now()
      if (tipo !== 'pantalla_completa_no_disponible') {
        if (ahora < ignorarHasta.current || ahora - ultimo.current < VENTANA_AGRUPACION_MS) return
        ultimo.current = ahora
      }
      try {
        const r = await api.post<RespuestaIncidente>(`/evaluacion/estudiante/evaluaciones/${evaluacionId}/incidentes/`, {
          tipo,
          detalle,
        })
        alResponderRef.current(r.data)
      } catch {
        // Sin conexión: el servidor no se entera; no se bloquea al estudiante por la red.
      }
    },
    [evaluacionId],
  )

  // Marca un periodo de gracia antes de pedir pantalla completa.
  const marcarCambioPantalla = useCallback(() => {
    ignorarHasta.current = Date.now() + GRACIA_PANTALLA_COMPLETA_MS
  }, [])

  useEffect(() => {
    if (!activo) return
    const bloquear = (e: Event) => e.preventDefault()
    const conIncidente = (tipo: TipoIncidente) => (e: Event) => {
      e.preventDefault()
      void reportar(tipo)
    }
    const alCopiar = conIncidente('copiar')
    const alCortar = conIncidente('cortar')
    const alPegar = conIncidente('pegar')
    const alMenu = conIncidente('menu_contextual')
    const alTeclear = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return
      const tecla = e.key.toLowerCase()
      if (!(tecla in ATAJOS)) return
      e.preventDefault()
      const tipo = ATAJOS[tecla]
      // A, P, S y U solo se bloquean; C, X y V además cuentan como incidente.
      if (tipo) void reportar(tipo, `Ctrl/Cmd+${tecla.toUpperCase()}`)
    }
    const alOcultar = () => {
      if (document.hidden) void reportar('cambio_pestana', 'La pestaña quedó oculta')
    }
    const alPerderFoco = () => void reportar('cambio_pestana', 'La ventana perdió el foco')
    const alCambiarPantalla = () => {
      if (!document.fullscreenElement) void reportar('salir_pantalla_completa')
    }

    document.addEventListener('copy', alCopiar)
    document.addEventListener('cut', alCortar)
    document.addEventListener('paste', alPegar)
    document.addEventListener('contextmenu', alMenu)
    document.addEventListener('dragstart', bloquear)
    document.addEventListener('selectstart', bloquear)
    document.addEventListener('keydown', alTeclear)
    document.addEventListener('visibilitychange', alOcultar)
    document.addEventListener('fullscreenchange', alCambiarPantalla)
    window.addEventListener('blur', alPerderFoco)
    return () => {
      document.removeEventListener('copy', alCopiar)
      document.removeEventListener('cut', alCortar)
      document.removeEventListener('paste', alPegar)
      document.removeEventListener('contextmenu', alMenu)
      document.removeEventListener('dragstart', bloquear)
      document.removeEventListener('selectstart', bloquear)
      document.removeEventListener('keydown', alTeclear)
      document.removeEventListener('visibilitychange', alOcultar)
      document.removeEventListener('fullscreenchange', alCambiarPantalla)
      window.removeEventListener('blur', alPerderFoco)
    }
  }, [activo, reportar])

  return { reportar, marcarCambioPantalla }
}
