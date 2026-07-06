// Botón toggle para alternar entre tema claro y oscuro.
// Persiste la preferencia en localStorage bajo la clave "theme".
// Al montar, lee la preferencia guardada o detecta la preferencia del sistema operativo.

import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

// Lee el tema inicial de localStorage o del sistema operativo.
// Se ejecuta una sola vez como initializer de useState.
function leerTemaInicial(): boolean {
  if (typeof window === 'undefined') return false
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') return true
  if (saved === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function ModeToggle() {
  const [isDark, setIsDark] = useState(leerTemaInicial)

  // Cuando cambia isDark, actualiza la clase en <html> y persiste en localStorage.
  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  return (
    <button
      type="button"
      onClick={() => setIsDark(prev => !prev)}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background text-foreground transition-colors hover:bg-muted"
    >
      {isDark ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
      <span className="sr-only">Cambiar tema</span>
    </button>
  )
}
