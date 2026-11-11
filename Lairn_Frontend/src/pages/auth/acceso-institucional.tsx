// Inicio de sesión con la cuenta Google institucional (HU-26).
//
// Carga Google Identity Services, dibuja el botón oficial y entrega el ID token al backend,
// que es quien lo verifica con Google y aplica las reglas (dominio institucional, cuenta
// existente y activa). El navegador nunca decide si alguien puede entrar.

import { useEffect, useRef, useState } from 'react'
import { ShieldCheck } from 'lucide-react'

interface GoogleId {
  initialize: (opciones: Record<string, unknown>) => void
  renderButton: (el: HTMLElement, opciones: Record<string, unknown>) => void
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } }
  }
}

const SCRIPT_GIS = 'https://accounts.google.com/gsi/client'

function cargarGis(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  return new Promise((resolver, rechazar) => {
    const existente = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT_GIS}"]`)
    const script = existente ?? Object.assign(document.createElement('script'), { src: SCRIPT_GIS, async: true, defer: true })
    script.addEventListener('load', () => resolver())
    script.addEventListener('error', () => rechazar(new Error('gis')))
    if (!existente) document.head.appendChild(script)
  })
}

export function BotonGoogle({
  clientId,
  dominios,
  alIngresar,
  deshabilitado,
}: {
  clientId: string
  dominios: string[]
  alIngresar: (credential: string) => void
  deshabilitado?: boolean
}) {
  const contenedor = useRef<HTMLDivElement>(null)
  const [error, setError] = useState(false)
  // La función de ingreso cambia en cada render; el botón de Google se inicializa una sola vez.
  const ingresar = useRef(alIngresar)
  useEffect(() => {
    ingresar.current = alIngresar
  }, [alIngresar])

  useEffect(() => {
    let vigente = true
    cargarGis()
      .then(() => {
        if (!vigente || !contenedor.current || !window.google) return
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (respuesta: { credential?: string }) => respuesta.credential && ingresar.current(respuesta.credential),
          // Sugerencia para el selector de cuentas; la regla real se valida en el servidor.
          hd: dominios[0],
          ux_mode: 'popup',
          cancel_on_tap_outside: true,
        })
        window.google.accounts.id.renderButton(contenedor.current, {
          type: 'standard', theme: 'outline', size: 'large', shape: 'pill', text: 'continue_with',
          logo_alignment: 'left', locale: 'es', width: contenedor.current.clientWidth || 320,
        })
      })
      .catch(() => vigente && setError(true))
    return () => {
      vigente = false
    }
  }, [clientId, dominios])

  return (
    <div className="space-y-2">
      <div
        ref={contenedor}
        className={deshabilitado ? 'pointer-events-none flex min-h-11 justify-center opacity-60' : 'flex min-h-11 justify-center'}
        aria-label="Continuar con Google"
      />
      {error && (
        <p className="text-center text-xs text-destructive">
          No se pudo cargar el inicio de sesión de Google. Revisa tu conexión y recarga la página.
        </p>
      )}
      <p className="flex items-start justify-center gap-1.5 text-center text-xs text-muted-foreground">
        <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" aria-hidden />
        Ingresa con tu correo institucional {dominios.map((d) => `@${d}`).join(', ')}
      </p>
    </div>
  )
}
