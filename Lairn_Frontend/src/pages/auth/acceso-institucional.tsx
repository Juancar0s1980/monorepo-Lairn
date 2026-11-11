// Inicio de sesión con la cuenta Google institucional (HU-26).
//
// Carga Google Identity Services, dibuja el botón oficial y entrega el ID token al backend,
// que es quien lo verifica con Google y aplica las reglas (dominio institucional, cuenta
// existente y activa). El navegador nunca decide si alguien puede entrar.

import { useEffect, useRef, useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'

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

// Logo «G» de Google (colores oficiales) para el botón de respaldo.
function LogoGoogle() {
  return (
    <svg viewBox="0 0 48 48" className="h-5 w-5" aria-hidden>
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.9 6.1C12.5 13.6 17.8 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.4 5.7c4.3-4 6.9-9.9 6.9-17.1z" />
      <path fill="#FBBC05" d="M10.6 28.6c-.5-1.4-.8-3-.8-4.6s.3-3.2.8-4.6l-7.9-6.1C1 16.6 0 20.2 0 24s1 7.4 2.7 10.7l7.9-6.1z" />
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.8-5.8l-7.4-5.7c-2.1 1.4-4.8 2.3-8.4 2.3-6.2 0-11.5-4.1-13.4-9.8l-7.9 6.1C6.6 42.6 14.6 48 24 48z" />
    </svg>
  )
}

// Se muestra mientras el servidor no tenga GOOGLE_CLIENT_ID: el acceso sigue siendo solo con Google,
// pero Google no puede abrir su ventana sin el ID de cliente.
export function BotonGoogleSinConfigurar({ dominios }: { dominios: string[] }) {
  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => toast.error('El inicio con Google aún no está configurado en el servidor (falta GOOGLE_CLIENT_ID).')}
        className="flex h-11 w-full items-center justify-center gap-3 rounded-full border border-border bg-white text-sm font-medium text-[#1f1f1f] shadow-sm transition hover:bg-[#f8f9fa] focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
      >
        <LogoGoogle />
        Continuar con Google
      </button>
      <p className="rounded-lg border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
        Falta configurar el ID de cliente de Google (GOOGLE_CLIENT_ID) en el servidor. Hasta entonces el botón no puede abrir la
        ventana de Google.
      </p>
      <p className="flex items-start justify-center gap-1.5 text-center text-xs text-muted-foreground">
        <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" aria-hidden />
        Solo se acepta tu correo institucional {dominios.map((d) => `@${d}`).join(', ')}
      </p>
    </div>
  )
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
        Solo se acepta tu correo institucional {dominios.map((d) => `@${d}`).join(', ')}
      </p>
    </div>
  )
}
