// Hook del banco de preguntas del docente: asignaturas asignadas, generación
// con IA, listado filtrado y curaduría (editar / aprobar / descartar).
//
// El backend solo devuelve asignaturas cuyo curso Lairn pertenece al docente;
// aquí no se filtra nada por seguridad, solo por conveniencia de la vista.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import type {
  AsignaturaDocente,
  EdicionPregunta,
  EstadoPregunta,
  PreguntaBanco,
} from '@/types/banco'
import { mensajeError } from '@/pages/academico/academico-utils'

// La IA tarda 20-90 s; el timeout global de Axios (15 s) cortaría la petición.
const TIMEOUT_GENERACION = 120000

export function useBancoPreguntas() {
  const [asignaturas, setAsignaturas] = useState<AsignaturaDocente[]>([])
  const [cargandoAsignaturas, setCargandoAsignaturas] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')

  // Selección para generar (HU-04.1).
  const [asignaturaId, setAsignaturaId] = useState('')
  const [resultadoId, setResultadoId] = useState('')
  const [competenciaId, setCompetenciaId] = useState('')
  const [cantidad, setCantidad] = useState(3)
  const [generando, setGenerando] = useState(false)

  // Listado y filtros (HU-05.1 / HU-04.5).
  const [estado, setEstado] = useState<EstadoPregunta>('pendiente')
  const [filtroCompetencia, setFiltroCompetencia] = useState('')
  const [preguntas, setPreguntas] = useState<PreguntaBanco[]>([])
  // Carga derivada: hay carga en curso mientras los filtros actuales no sean
  // los de la última respuesta (evita setState síncrono dentro de efectos).
  const clavePreguntas = `${asignaturaId}|${estado}|${filtroCompetencia}`
  const [claveCargada, setClaveCargada] = useState('')
  const cargandoPreguntas = !!asignaturaId && claveCargada !== clavePreguntas
  // Id de la pregunta con una acción en curso (evita dobles envíos).
  const [procesandoId, setProcesandoId] = useState<number | null>(null)
  const [editando, setEditando] = useState<PreguntaBanco | null>(null)
  const [descartando, setDescartando] = useState<PreguntaBanco | null>(null)

  const asignatura = useMemo(
    () => asignaturas.find((a) => String(a.id) === asignaturaId) ?? null,
    [asignaturas, asignaturaId],
  )

  // Contadores que disparan una recarga desde manejadores de eventos (patrón del
  // proyecto: la petición vive dentro del efecto, nunca setState síncrono en él).
  const [intentoAsignaturas, setIntentoAsignaturas] = useState(0)
  const [versionPreguntas, setVersionPreguntas] = useState(0)

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<AsignaturaDocente[]>('/evaluacion/docente/asignaturas/')
        if (!activo) return
        const lista = Array.isArray(res.data) ? res.data : []
        setErrorCarga('')
        setAsignaturas(lista)
        if (lista.length) setAsignaturaId((actual) => actual || String(lista[0].id))
      } catch (err: unknown) {
        if (activo) setErrorCarga(mensajeError(err, 'No se pudieron cargar tus asignaturas.'))
      } finally {
        if (activo) setCargandoAsignaturas(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [intentoAsignaturas])

  // Reintento manual tras un error de carga.
  const cargarAsignaturas = () => {
    setCargandoAsignaturas(true)
    setIntentoAsignaturas((n) => n + 1)
  }

  useEffect(() => {
    if (!asignaturaId) return
    // `activo` descarta respuestas viejas si el docente cambia de filtro rápido.
    let activo = true
    const clave = `${asignaturaId}|${estado}|${filtroCompetencia}`
    const cargar = async () => {
      try {
        const params = new URLSearchParams({ estado, asignatura: asignaturaId })
        if (filtroCompetencia) params.set('competencia_transversal', filtroCompetencia)
        const res = await api.get<PreguntaBanco[]>(`/evaluacion/docente/banco/?${params}`)
        if (activo) setPreguntas(Array.isArray(res.data) ? res.data : [])
      } catch (err: unknown) {
        if (activo) toast.error(mensajeError(err, 'No se pudieron cargar las preguntas'))
      } finally {
        if (activo) setClaveCargada(clave)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [asignaturaId, estado, filtroCompetencia, versionPreguntas])

  const recargarPreguntas = () => setVersionPreguntas((n) => n + 1)

  // Al cambiar de asignatura, el RA y la competencia elegidos ya no aplican.
  const elegirAsignatura = (id: string) => {
    setAsignaturaId(id)
    setResultadoId('')
    setCompetenciaId('')
    setFiltroCompetencia('')
  }

  const generar = async () => {
    if (!asignaturaId || !resultadoId || generando) return
    setGenerando(true)
    try {
      const res = await api.post<PreguntaBanco[]>(
        '/evaluacion/docente/banco/generar/',
        {
          asignatura: Number(asignaturaId),
          resultado: Number(resultadoId),
          competencia_transversal: competenciaId ? Number(competenciaId) : null,
          cantidad,
        },
        { timeout: TIMEOUT_GENERACION },
      )
      toast.success(`${res.data.length} pregunta(s) lista(s) para revisar`)
      // Las nuevas quedan pendientes: se muestra esa lista.
      if (estado !== 'pendiente') setEstado('pendiente')
      else recargarPreguntas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudieron generar las preguntas'))
    } finally {
      setGenerando(false)
    }
  }

  const guardarEdicion = async (id: number, datos: EdicionPregunta) => {
    setProcesandoId(id)
    try {
      await api.patch(`/evaluacion/docente/banco/${id}/`, datos)
      toast.success('Cambios guardados')
      setEditando(null)
      recargarPreguntas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudieron guardar los cambios'))
    } finally {
      setProcesandoId(null)
    }
  }

  const aprobar = async (id: number) => {
    setProcesandoId(id)
    try {
      await api.post(`/evaluacion/docente/banco/${id}/aprobar/`)
      toast.success('Pregunta aprobada: ya forma parte del banco oficial')
      recargarPreguntas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo aprobar la pregunta'))
    } finally {
      setProcesandoId(null)
    }
  }

  const descartar = async (id: number, motivo: string) => {
    setProcesandoId(id)
    try {
      await api.post(`/evaluacion/docente/banco/${id}/descartar/`, { motivo })
      toast.success('Pregunta descartada')
      setDescartando(null)
      recargarPreguntas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo descartar la pregunta'))
    } finally {
      setProcesandoId(null)
    }
  }

  return {
    asignaturas, cargandoAsignaturas, errorCarga, cargarAsignaturas,
    asignaturaId, elegirAsignatura, asignatura,
    resultadoId, setResultadoId, competenciaId, setCompetenciaId, cantidad, setCantidad,
    generando, generar,
    estado, setEstado, filtroCompetencia, setFiltroCompetencia,
    preguntas, cargandoPreguntas, procesandoId,
    editando, setEditando, guardarEdicion,
    descartando, setDescartando, descartar, aprobar,
  }
}

export type BancoPreguntas = ReturnType<typeof useBancoPreguntas>
