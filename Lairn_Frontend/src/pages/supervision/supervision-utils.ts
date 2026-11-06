// Utilidades compartidas de supervisión en sala (ADR-009): etiquetas y
// colores de asistencia, formato de tiempo, consulta periódica (cada 10 s) y
// reloj sincronizado con el servidor. Los componentes están en
// `componentes-supervision.tsx`.

import { useCallback, useEffect, useRef, useState } from 'react'
import type { ConsecuenciaIncidente, EstadoAsistencia, EstadoIntegridad, TipoExcusa, TipoIncidente } from '@/types/supervision'

export const INTERVALO_REFRESCO_MS = 10_000

export const ETIQUETA_ASISTENCIA: Record<EstadoAsistencia, string> = {
  presente: 'Presente',
  tarde: 'Tarde',
  ausente: 'Ausente',
  excusa: 'Excusa',
}

export const CLASE_ASISTENCIA: Record<EstadoAsistencia, string> = {
  presente: 'bg-success/10 text-success',
  tarde: 'bg-warning/15 text-foreground',
  ausente: 'bg-destructive/10 text-destructive',
  excusa: 'bg-primary/10 text-primary',
}

export const ETIQUETA_EXCUSA: Record<TipoExcusa, string> = {
  permiso_medico: 'Permiso médico',
  calamidad: 'Calamidad doméstica',
  institucional: 'Actividad institucional',
  otra: 'Otra',
}

// Integridad académica (ADR-010).
export const ETIQUETA_INTEGRIDAD: Record<EstadoIntegridad, string> = {
  normal: 'Normal',
  advertido: 'Advertido',
  suspendido: 'Suspendido',
  reactivado: 'Reactivado',
  anulado_fraude: 'Anulado por fraude',
}

export const CLASE_INTEGRIDAD: Record<EstadoIntegridad, string> = {
  normal: 'bg-muted text-muted-foreground',
  advertido: 'bg-warning/15 text-foreground',
  suspendido: 'bg-destructive text-white',
  reactivado: 'bg-primary/10 text-primary',
  anulado_fraude: 'bg-destructive/10 text-destructive',
}

export const ETIQUETA_INCIDENTE: Record<TipoIncidente, string> = {
  copiar: 'Copiar',
  cortar: 'Cortar',
  pegar: 'Pegar',
  menu_contextual: 'Menú contextual',
  cambio_pestana: 'Cambio de pestaña o ventana',
  salir_pantalla_completa: 'Salió de pantalla completa',
  pantalla_completa_no_disponible: 'Pantalla completa no disponible',
}

export const ETIQUETA_CONSECUENCIA: Record<ConsecuenciaIncidente, string> = {
  advertencia: 'advertencia',
  suspension: 'suspensión',
  agrupado: 'agrupado, no cuenta',
  sin_efecto: 'informativo',
}

export const formatoHoraSegundos = new Intl.DateTimeFormat('es-CO', { timeStyle: 'medium' })

export const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
export const formatoHora = new Intl.DateTimeFormat('es-CO', { timeStyle: 'short' })

export function reloj(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const dos = (n: number) => String(n).padStart(2, '0')
  return h ? `${h}:${dos(m)}:${dos(s)}` : `${dos(m)}:${dos(s)}`
}

// Hora del servidor que avanza cada segundo: el reloj del navegador puede estar
// desfasado. `sincronizar` se llama con `ahora_servidor` de cada respuesta.
export function useRelojServidor() {
  const [desfase, setDesfase] = useState(0)
  const [ahora, setAhora] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setAhora(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])
  const sincronizar = useCallback((iso: string) => {
    setDesfase(new Date(iso).getTime() - Date.now())
    setAhora(Date.now())
  }, [])
  return { ahoraServidor: ahora + desfase, sincronizar }
}

// Ejecuta `cargar` al montar y cada 10 s mientras `activo`. Cambiar `clave`
// fuerza una consulta inmediata (p. ej. tras un cargue).
export function useConsultaPeriodica(cargar: () => Promise<void>, activo = true, clave: unknown = 0) {
  const ref = useRef(cargar)
  useEffect(() => {
    ref.current = cargar
  })
  useEffect(() => {
    if (!activo) return
    void ref.current()
    const id = window.setInterval(() => void ref.current(), INTERVALO_REFRESCO_MS)
    return () => window.clearInterval(id)
  }, [activo, clave])
}
