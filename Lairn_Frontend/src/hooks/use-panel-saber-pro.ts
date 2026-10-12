// Hook para obtener el panel del módulo Saber Pro (HU-16).
//
// Llama a GET /saber-pro/panel/, que resuelve del lado del backend qué
// funcionalidades mostrar según el rol del usuario autenticado (Docente o
// Estudiante). No depende de ningún curso.

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { PanelSaberPro } from '@/types/saber-pro'

interface ResultadoUsePanelSaberPro {
  panel: PanelSaberPro | null
  cargando: boolean
  error: string | null
}

export function usePanelSaberPro(): ResultadoUsePanelSaberPro {
  const [panel, setPanel] = useState<PanelSaberPro | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  return { panel, cargando, error }
}