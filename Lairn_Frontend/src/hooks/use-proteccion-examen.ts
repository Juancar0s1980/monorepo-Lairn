// Hook de protección preventiva para exámenes y simulacros (HU-22).
//
// Mientras `activo` sea verdadero:
//   - bloquea copiar, cortar, pegar, arrastrar, soltar y el menú contextual;
//   - intenta mantener la pantalla del examen en modo completo desde el inicio
//     del intento y detecta cuando se sale de él;
//   - detecta cuando la ventana pierde el foco o la pestaña se oculta y llama a
//     `onSalida` para que la página bloquee el intento en el backend;
//   - advierte antes de cerrar o recargar la página.
//
// El navegador no permite impedir por código el cambio de pestaña o la
// minimización. Por eso se detecta la salida, se bloquea el intento en el
// servidor y se exige el código del docente para reanudarlo.

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  salirDePantallaCompleta,
  solicitarPantallaCompleta,
} from '@/utilities/pantalla-completa'

interface OpcionesProteccionExamen {
  activo: boolean
  onSalida?: () => void
}

interface ResultadoProteccionExamen {
  fueraDeFoco: boolean
  reiniciarProteccion: () => void
}

export function useProteccionExamen({
  activo,
  onSalida,
}: OpcionesProteccionExamen): ResultadoProteccionExamen {
  const [salidaDetectada, setSalidaDetectada] = useState(false)
  const pantallaCompletaSolicitada = useRef(false)
  const salidaNotificada = useRef(false)
  const onSalidaRef = useRef(onSalida)

  useEffect(() => {
    onSalidaRef.current = onSalida
  }, [onSalida])

  const notificarSalida = useCallback(() => {
    setSalidaDetectada(true)
    if (salidaNotificada.current) return
    salidaNotificada.current = true
    onSalidaRef.current?.()
  }, [])

  const reiniciarProteccion = useCallback(() => {
    salidaNotificada.current = false
    setSalidaDetectada(false)
    solicitarPantallaCompleta()
  }, [])

  useEffect(() => {
    if (!activo) return

    pantallaCompletaSolicitada.current = Boolean(document.fullscreenElement)
    salidaNotificada.current = false

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
      if (document.hidden) notificarSalida()
    }

    const detectarPantallaCompleta = () => {
      if (pantallaCompletaSolicitada.current && !document.fullscreenElement) {
        notificarSalida()
      }
    }

    const solicitarEnPrimeraInteraccion = () => {
      if (pantallaCompletaSolicitada.current) return
      pantallaCompletaSolicitada.current = true
      solicitarPantallaCompleta()
    }

    const manejarTeclado = (evento: KeyboardEvent) => {
      solicitarEnPrimeraInteraccion()

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
    document.addEventListener('pointerdown', solicitarEnPrimeraInteraccion, { once: true })
    document.addEventListener('keydown', manejarTeclado)
    window.addEventListener('blur', notificarSalida)
    window.addEventListener('beforeunload', advertirCierre)

    return () => {
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
      document.removeEventListener('pointerdown', solicitarEnPrimeraInteraccion)
      document.removeEventListener('keydown', manejarTeclado)
      window.removeEventListener('blur', notificarSalida)
      window.removeEventListener('beforeunload', advertirCierre)
      salirDePantallaCompleta()
    }
  }, [activo, notificarSalida])

  return {
    fueraDeFoco: activo && salidaDetectada,
    reiniciarProteccion,
  }
}
