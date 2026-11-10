// Hook de protección estricta para exámenes y simulacros (HU-22).
//
// Mientras `activo` sea verdadero:
//   - bloquea copiar, cortar, pegar, arrastrar, soltar y el menú contextual;
//   - intenta mantener la pantalla del examen en modo completo desde el inicio
//     del intento y detecta cuando se sale de él;
//   - detecta cambio de pestaña, minimización o pérdida de foco y llama a
//     `onBloqueo` para que la página solicite el desbloqueo remoto del docente
//     sin finalizar el intento;
//   - intercepta el botón "atrás" del navegador y los enlaces internos para
//     avisar que salir envía el intento (`onIntentoRetroceso`);
//   - en `pagehide` usa `onSalidaInminente` para enviar el intento con
//     keepalive aunque la página se esté cerrando;
//   - advierte antes de cerrar o recargar la página.
//
// Mientras `bloqueado` sea verdadero no se envían nuevas solicitudes ni se
// vuelve a pedir pantalla completa. Al desbloquearse, el siguiente gesto del
// estudiante recupera el modo completo.

import { useEffect, useRef } from 'react'
import {
  salirDePantallaCompleta,
  solicitarPantallaCompleta,
} from '@/utilities/pantalla-completa'

const CLAVE_ESTADO = 'examenSaberPro'

export type MotivoBloqueoExamen =
  | 'cambio_pestana'
  | 'pantalla_completa'
  | 'perdida_foco'

interface OpcionesProteccionExamen {
  activo: boolean
  bloqueado?: boolean
  onBloqueo?: (motivo: MotivoBloqueoExamen) => void
  onIntentoRetroceso?: () => void
  onSalidaInminente?: () => void
}

export function useProteccionExamen({
  activo,
  bloqueado = false,
  onBloqueo,
  onIntentoRetroceso,
  onSalidaInminente,
}: OpcionesProteccionExamen): void {
  const onBloqueoRef = useRef(onBloqueo)
  const onIntentoRetrocesoRef = useRef(onIntentoRetroceso)
  const onSalidaInminenteRef = useRef(onSalidaInminente)
  const bloqueadoRef = useRef(bloqueado)

  useEffect(() => {
    onBloqueoRef.current = onBloqueo
    onIntentoRetrocesoRef.current = onIntentoRetroceso
    onSalidaInminenteRef.current = onSalidaInminente
  }, [onBloqueo, onIntentoRetroceso, onSalidaInminente])

  useEffect(() => {
    bloqueadoRef.current = bloqueado
  }, [bloqueado])

  useEffect(() => {
    if (!activo) return

    let ultimoBloqueo = 0
    let temporizadorBlur: number | undefined

    // Evita solicitudes duplicadas cuando visibilitychange, fullscreenchange y
    // blur se disparan casi al mismo tiempo por una sola salida.
    const notificarBloqueo = (motivo: MotivoBloqueoExamen) => {
      if (bloqueadoRef.current) return
      const ahora = Date.now()
      if (ahora - ultimoBloqueo < 1500) return
      ultimoBloqueo = ahora
      onBloqueoRef.current?.(motivo)
    }

    // Marca la entrada actual y agrega una entrada duplicada de la misma URL.
    // Así el botón "atrás" no cambia de ruta (React Router sigue mostrando el
    // examen) y podemos interceptarlo para mostrar el aviso antes de salir.
    const estadoActual = (window.history.state ?? {}) as Record<string, unknown>
    window.history.replaceState({ ...estadoActual, [CLAVE_ESTADO]: true }, '')
    window.history.pushState({ [CLAVE_ESTADO]: true }, '')

    const manejarPopState = () => {
      window.history.pushState({ [CLAVE_ESTADO]: true }, '')
      onIntentoRetrocesoRef.current?.()
    }

    const interceptarNavegacion = (evento: MouseEvent) => {
      if (
        evento.defaultPrevented ||
        evento.button !== 0 ||
        evento.metaKey ||
        evento.ctrlKey ||
        evento.shiftKey ||
        evento.altKey
      ) {
        return
      }

      const objetivo = evento.target as HTMLElement | null
      const enlace = objetivo?.closest('a[href]') as HTMLAnchorElement | null
      if (!enlace) return

      const href = enlace.getAttribute('href')
      if (
        !href ||
        href.startsWith('#') ||
        enlace.target === '_blank' ||
        enlace.hasAttribute('download')
      ) {
        return
      }

      evento.preventDefault()
      evento.stopPropagation()
      onIntentoRetrocesoRef.current?.()
    }

    const bloquearEvento = (evento: Event) => {
      evento.preventDefault()
      evento.stopPropagation()
    }

    const bloquearEntrada = (evento: Event) => {
      const entrada = evento as InputEvent
      if (
        entrada.inputType === 'insertFromPaste' ||
        entrada.inputType === 'insertFromDrop'
      ) {
        bloquearEvento(evento)
      }
    }

    const desactivarArrastre = (evento: DragEvent) => {
      if (evento.dataTransfer) evento.dataTransfer.dropEffect = 'none'
    }

    const detectarVisibilidad = () => {
      if (document.hidden) notificarBloqueo('cambio_pestana')
    }

    const detectarPantallaCompleta = () => {
      if (!document.fullscreenElement) notificarBloqueo('pantalla_completa')
    }

    // El blur puede dispararse al abrir el diálogo del navegador o al hacer clic
    // en la barra de direcciones. Esperamos un instante: si el foco vuelve, no
    // se bloquea el intento; si no vuelve (cambio de aplicación), se solicita
    // el desbloqueo remoto.
    const detectarBlur = () => {
      if (temporizadorBlur !== undefined) window.clearTimeout(temporizadorBlur)
      temporizadorBlur = window.setTimeout(() => {
        temporizadorBlur = undefined
        notificarBloqueo('perdida_foco')
      }, 600)
    }

    const detectarFoco = () => {
      if (temporizadorBlur === undefined) return
      window.clearTimeout(temporizadorBlur)
      temporizadorBlur = undefined
    }

    const solicitarEnInteraccion = () => {
      if (bloqueadoRef.current || document.fullscreenElement) return
      solicitarPantallaCompleta()
    }

    const manejarTeclado = (evento: KeyboardEvent) => {
      solicitarEnInteraccion()

      const tecla = evento.key.toLowerCase()
      const conModificador = evento.ctrlKey || evento.metaKey
      const esAtajoDePortapapeles =
        (conModificador && (tecla === 'c' || tecla === 'x' || tecla === 'v')) ||
        (evento.shiftKey && tecla === 'insert') ||
        (conModificador && tecla === 'insert')

      if (esAtajoDePortapapeles) bloquearEvento(evento)
    }

    const advertirCierre = (evento: BeforeUnloadEvent) => {
      evento.preventDefault()
      evento.returnValue = ''
    }

    const manejarPageHide = () => {
      onSalidaInminenteRef.current?.()
    }

    document.addEventListener('click', interceptarNavegacion, true)
    document.addEventListener('copy', bloquearEvento)
    document.addEventListener('cut', bloquearEvento)
    document.addEventListener('paste', bloquearEvento)
    document.addEventListener('contextmenu', bloquearEvento)
    document.addEventListener('dragstart', bloquearEvento)
    document.addEventListener('drop', bloquearEvento)
    document.addEventListener('dragover', desactivarArrastre)
    document.addEventListener('beforeinput', bloquearEntrada)
    document.addEventListener('visibilitychange', detectarVisibilidad)
    document.addEventListener('fullscreenchange', detectarPantallaCompleta)
    document.addEventListener('pointerdown', solicitarEnInteraccion)
    document.addEventListener('keydown', manejarTeclado)
    window.addEventListener('popstate', manejarPopState)
    window.addEventListener('blur', detectarBlur)
    window.addEventListener('focus', detectarFoco)
    window.addEventListener('beforeunload', advertirCierre)
    window.addEventListener('pagehide', manejarPageHide)

    return () => {
      document.removeEventListener('click', interceptarNavegacion, true)
      document.removeEventListener('copy', bloquearEvento)
      document.removeEventListener('cut', bloquearEvento)
      document.removeEventListener('paste', bloquearEvento)
      document.removeEventListener('contextmenu', bloquearEvento)
      document.removeEventListener('dragstart', bloquearEvento)
      document.removeEventListener('drop', bloquearEvento)
      document.removeEventListener('dragover', desactivarArrastre)
      document.removeEventListener('beforeinput', bloquearEntrada)
      document.removeEventListener('visibilitychange', detectarVisibilidad)
      document.removeEventListener('fullscreenchange', detectarPantallaCompleta)
      document.removeEventListener('pointerdown', solicitarEnInteraccion)
      document.removeEventListener('keydown', manejarTeclado)
      window.removeEventListener('popstate', manejarPopState)
      window.removeEventListener('blur', detectarBlur)
      window.removeEventListener('focus', detectarFoco)
      window.removeEventListener('beforeunload', advertirCierre)
      window.removeEventListener('pagehide', manejarPageHide)

      if (temporizadorBlur !== undefined) window.clearTimeout(temporizadorBlur)

      const estado = window.history.state as Record<string, unknown> | null
      if (estado && estado[CLAVE_ESTADO]) {
        const copia = { ...estado }
        delete copia[CLAVE_ESTADO]
        window.history.replaceState(copia, '')
      }

      salirDePantallaCompleta()
    }
  }, [activo])
}
