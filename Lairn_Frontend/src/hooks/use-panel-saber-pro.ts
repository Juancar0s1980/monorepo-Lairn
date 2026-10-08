// Hook para obtener el panel del módulo Saber Pro (HU-16).
//
// Llama a GET /saber-pro/panel/, que resuelve del lado del backend qué
// funcionalidades mostrar según el rol del usuario autenticado (Docente o
// Estudiante). No depende de ningún curso. Expone `recargar()` para refrescar
// el panel tras una mutación (p. ej. el estudiante se une a un curso con código
// y `tiene_cursos` pasa a true, HU-18.3).

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { PanelSaberPro } from '@/types/saber-pro'

interface ResultadoUsePanelSaberPro {
  panel: PanelSaberPro | null
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function usePanelSaberPro(): ResultadoUsePanelSaberPro {
  const [panel, setPanel] = useState<PanelSaberPro | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Recarga el panel desde el backend (se usa tras unirse a un curso con código).
  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      const { data } = await api.get<PanelSaberPro>('/saber-pro/panel/')
      setPanel(data)
      setError(null)
    } catch {
      setError('No se pudo cargar el panel de Saber Pro.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    let activo = true

    async function cargar() {
      try {
        const { data } = await api.get<PanelSaberPro>('/saber-pro/panel/')
        if (activo) setPanel(data)
      } catch {
        if (activo) setError('No se pudo cargar el panel de Saber Pro.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
    }
  }, [])

  return { panel, cargando, error, recargar }
}