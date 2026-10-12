// Hook para listar el banco de contenido del docente para el área de un curso (HU-20).
//
// Llama a GET /saber-pro/docente/cursos/{id}/contenido/ (sin query param `estado`)
// para traer todo el banco del área del curso; la página separa en cliente las
// pestañas de "Pendientes" y "Aprobados". Expone `recargar()` para refrescar
// tras generar, editar, aprobar o descartar contenido.

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { ContenidoBancoSaberPro } from '@/types/saber-pro'

interface ResultadoUseContenidoBancoSaberPro {
  contenidos: ContenidoBancoSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useContenidoBancoSaberPro(cursoId: number | null): ResultadoUseContenidoBancoSaberPro {
  const [contenidos, setContenidos] = useState<ContenidoBancoSaberPro[]>([])
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  // Recarga el banco desde el backend (se usa tras cada mutación de contenido).
  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const { data } = await api.get<ContenidoBancoSaberPro[]>(
        `/saber-pro/docente/cursos/${cursoId}/contenido/`
      )
      setContenidos(data)
      setError(null)
    } catch {
      setError('No se pudo cargar el banco de contenido.')
    } finally {
      setCargando(false)
    }
  }, [cursoId])

  useEffect(() => {
    // AbortController + flag: evita setState tras desmontar o al cambiar de curso.
    // Toda la actualización de estado vive dentro del cargador async para no
    // disparar setState síncrono en el cuerpo del efecto.
    const controlador = new AbortController()
    let activo = true

    async function cargar() {
      if (cursoId === null) {
        setContenidos([])
        setCargando(false)
        setError(null)
        return
      }
      setCargando(true)
      try {
        const { data } = await api.get<ContenidoBancoSaberPro[]>(
          `/saber-pro/docente/cursos/${cursoId}/contenido/`,
          { signal: controlador.signal }
        )
        if (activo) {
          setContenidos(data)
          setError(null)
        }
      } catch {
        if (activo) setError('No se pudo cargar el banco de contenido.')
      } finally {
        if (activo) setCargando(false)
      }
    }

    cargar()
    return () => {
      activo = false
      controlador.abort()
    }
  }, [cursoId])

  return { contenidos, cargando, error, recargar }
}