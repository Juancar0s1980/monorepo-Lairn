// Hook para listar el banco de contenido del docente para el área de un curso (HU-20).
//
// Llama a GET /saber-pro/docente/cursos/{id}/contenido/ con filtros opcionales
// (estado, competencia_id, afirmacion_id, evidencia_id, parte) para traer el
// banco del área. Permite recargar tras generar, editar, aprobar o descartar
// contenido sin perder los filtros activos.

import { useState, useEffect, useCallback } from 'react'
import api from '@/services/api'
import type { ContenidoBancoSaberPro } from '@/types/saber-pro'

export interface FiltrosContenidoBanco {
  estado?: 'pendiente' | 'aprobado' | 'todos'
  competenciaId?: number | null
  afirmacionId?: number | null
  evidenciaId?: number | null
  parte?: number | null
}

interface ResultadoUseContenidoBancoSaberPro {
  contenidos: ContenidoBancoSaberPro[]
  cargando: boolean
  error: string | null
  recargar: () => Promise<void>
}

export function useContenidoBancoSaberPro(
  cursoId: number | null,
  filtros: FiltrosContenidoBanco = {}
): ResultadoUseContenidoBancoSaberPro {
  const [contenidos, setContenidos] = useState<ContenidoBancoSaberPro[]>([])
  const [cargando, setCargando] = useState(Boolean(cursoId))
  const [error, setError] = useState<string | null>(null)

  const construirParametros = useCallback(() => {
    const params = new URLSearchParams()
    if (filtros.estado && filtros.estado !== 'todos') {
      params.append('estado', filtros.estado)
    }
    if (filtros.competenciaId) {
      params.append('competencia_id', String(filtros.competenciaId))
    }
    if (filtros.afirmacionId) {
      params.append('afirmacion_id', String(filtros.afirmacionId))
    }
    if (filtros.evidenciaId) {
      params.append('evidencia_id', String(filtros.evidenciaId))
    }
    if (filtros.parte) {
      params.append('parte', String(filtros.parte))
    }
    return params
  }, [filtros.afirmacionId, filtros.competenciaId, filtros.estado, filtros.evidenciaId, filtros.parte])

  const recargar = useCallback(async () => {
    if (cursoId === null) return
    setCargando(true)
    try {
      const params = construirParametros()
      const query = params.toString()
      const url = query
        ? `/saber-pro/docente/cursos/${cursoId}/contenido/?${query}`
        : `/saber-pro/docente/cursos/${cursoId}/contenido/`
      const { data } = await api.get<ContenidoBancoSaberPro[]>(url)
      setContenidos(data)
      setError(null)
    } catch {
      setError('No se pudo cargar el banco de contenido.')
    } finally {
      setCargando(false)
    }
  }, [construirParametros, cursoId])

  useEffect(() => {
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
        const params = construirParametros()
        const query = params.toString()
        const url = query
          ? `/saber-pro/docente/cursos/${cursoId}/contenido/?${query}`
          : `/saber-pro/docente/cursos/${cursoId}/contenido/`
        const { data } = await api.get<ContenidoBancoSaberPro[]>(url, {
          signal: controlador.signal,
        })
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
  }, [construirParametros, cursoId])

  return { contenidos, cargando, error, recargar }
}