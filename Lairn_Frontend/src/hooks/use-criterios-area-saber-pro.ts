// Hook para obtener los criterios de evaluación de un área Saber Pro (HU-20.1).
//
// Llama a GET /saber-pro/docente/areas/{id}/criterios/, que resuelve la
// estructura del área (`competencias`, `partes` o `consigna`) y los criterios
// seleccionables al generar contenido con IA. Se recarga cuando cambia el área.
// El formulario de generación se apoya en esta respuesta para no duplicar en el
// cliente la forma de cada área (esa vive en el backend).

import { useState, useEffect } from 'react'
import api from '@/services/api'
import type { CriteriosAreaSaberPro } from '@/types/saber-pro'

interface ResultadoUseCriteriosAreaSaberPro {
  criterios: CriteriosAreaSaberPro | null
  cargando: boolean
  error: string | null
}

export function useCriteriosAreaSaberPro(areaId: number | null): ResultadoUseCriteriosAreaSaberPro {
  const [criterios, setCriterios] = useState<CriteriosAreaSaberPro | null>(null)
  const [cargando, setCargando] = useState(Boolean(areaId))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // AbortController + flag: evita setState tras desmontar o al cambiar de área
    // rápidamente (StrictMode re-monta en desarrollo). Toda la actualización de
    // estado vive dentro del cargador async (sin setState síncrono en el efecto).
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (areaId === null) {
        setCriterios(null)
        setCargando(false)
        setError(null)
        return
      }
      setCargando(true)
      try {
        const { data } = await api.get<CriteriosAreaSaberPro>(
          `/saber-pro/docente/areas/${areaId}/criterios/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setCriterios(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudieron cargar los criterios del área.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [areaId])

  return { criterios, cargando, error }
}