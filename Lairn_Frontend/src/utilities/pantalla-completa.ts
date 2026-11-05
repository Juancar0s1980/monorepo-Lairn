export function solicitarPantallaCompleta(): void {
  if (typeof document === 'undefined' || document.fullscreenElement) return
  try {
    const solicitud = document.documentElement.requestFullscreen?.()
    void solicitud?.catch(() => undefined)
  } catch {
    // Algunos navegadores no permiten pantalla completa fuera de un gesto directo.
  }
}

export function salirDePantallaCompleta(): void {
  if (typeof document === 'undefined' || !document.fullscreenElement) return
  try {
    void document.exitFullscreen?.().catch(() => undefined)
  } catch {
    // Si el navegador ya salió del modo completo, no hay nada que hacer.
  }
}
