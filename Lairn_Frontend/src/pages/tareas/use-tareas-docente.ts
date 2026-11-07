// Hook de "Tareas" del docente (HU-08B): asignaturas, lista de tareas,
// borrador abierto en el editor, archivos guía, publicación, panel de
// entregas y calificación por rúbrica.
//
// Las cargas viven dentro de efectos (patrón del proyecto) y se repiten con
// contadores de versión desde los manejadores de eventos.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import type { AsignaturaDocente } from '@/types/banco'
import type { CriterioRubrica, FilaEntrega, FormatoEntrega, Tarea } from '@/types/tarea'
import { mensajeError } from '@/pages/academico/academico-utils'
import { aEntradaLocal } from '@/pages/academico/use-evaluacion-formal'
import { RUBRICA_INICIAL } from './utilidades-tareas'

const TIMEOUT_IA = 120000

export interface FormTarea {
  resultado: string
  titulo: string
  descripcion: string
  formatos_permitidos: FormatoEntrega[]
  fecha_limite: string
  permite_tardias: boolean
  rubrica: CriterioRubrica[]
}

const FORM_VACIO: FormTarea = {
  resultado: '',
  titulo: '',
  descripcion: '',
  formatos_permitidos: ['pdf'],
  fecha_limite: '',
  permite_tardias: false,
  rubrica: RUBRICA_INICIAL,
}

function formDesde(t: Tarea): FormTarea {
  return {
    resultado: String(t.resultado),
    titulo: t.titulo,
    descripcion: t.descripcion,
    formatos_permitidos: t.formatos_permitidos,
    fecha_limite: aEntradaLocal(t.fecha_limite),
    permite_tardias: t.permite_tardias,
    rubrica: t.rubrica.length ? t.rubrica : RUBRICA_INICIAL,
  }
}

export function useTareasDocente() {
  const [asignaturas, setAsignaturas] = useState<AsignaturaDocente[]>([])
  const [asignaturaId, setAsignaturaId] = useState('')
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')

  const [tareas, setTareas] = useState<Tarea[]>([])
  const [versionTareas, setVersionTareas] = useState(0)
  // Tarea abierta: id existente o 'nueva'.
  const [abiertaId, setAbiertaId] = useState<number | 'nueva' | null>(null)
  const [form, setForm] = useState<FormTarea>(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [publicando, setPublicando] = useState(false)
  const [subiendo, setSubiendo] = useState(false)
  const [generando, setGenerando] = useState(false)

  const [entregas, setEntregas] = useState<FilaEntrega[]>([])
  const [versionEntregas, setVersionEntregas] = useState(0)
  const [calificando, setCalificando] = useState<FilaEntrega | null>(null)
  const [guardandoNota, setGuardandoNota] = useState(false)
  // Entregas que la IA está analizando y avance del análisis en lote (HU-15.1).
  const [analizando, setAnalizando] = useState<number[]>([])
  const [progresoIA, setProgresoIA] = useState<{ hechas: number; total: number } | null>(null)

  const asignatura = useMemo(
    () => asignaturas.find((a) => String(a.id) === asignaturaId) ?? null,
    [asignaturas, asignaturaId],
  )
  const abierta = useMemo(() => tareas.find((t) => t.id === abiertaId) ?? null, [tareas, abiertaId])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<AsignaturaDocente[]>('/evaluacion/docente/asignaturas/')
        if (!activo) return
        setAsignaturas(res.data)
        if (res.data.length) setAsignaturaId((a) => a || String(res.data[0].id))
      } catch (err: unknown) {
        if (activo) setErrorCarga(mensajeError(err, 'No se pudieron cargar tus asignaturas.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [])

  useEffect(() => {
    if (!asignaturaId) return
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<Tarea[]>(`/evaluacion/docente/tareas/?asignatura=${asignaturaId}`)
        if (activo) setTareas(res.data)
      } catch (err: unknown) {
        if (activo) toast.error(mensajeError(err, 'No se pudieron cargar las tareas'))
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [asignaturaId, versionTareas])

  // El panel de entregas solo aplica a tareas publicadas.
  const idEntregas = abierta?.estado === 'publicada' ? abierta.id : null
  useEffect(() => {
    if (idEntregas === null) return
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<FilaEntrega[]>(`/evaluacion/docente/tareas/${idEntregas}/entregas/`)
        if (activo) setEntregas(res.data)
      } catch (err: unknown) {
        if (activo) toast.error(mensajeError(err, 'No se pudieron cargar las entregas'))
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [idEntregas, versionEntregas])

  const recargarTareas = () => setVersionTareas((n) => n + 1)

  const elegirAsignatura = (id: string) => {
    setAsignaturaId(id)
    setAbiertaId(null)
  }

  const nueva = () => {
    setAbiertaId('nueva')
    setForm({ ...FORM_VACIO, resultado: asignatura?.resultados[0] ? String(asignatura.resultados[0].id) : '' })
  }

  const abrir = (t: Tarea) => {
    setAbiertaId(t.id)
    setForm(formDesde(t))
    setEntregas([])
  }

  const cuerpo = () => ({
    asignatura: Number(asignaturaId),
    resultado: Number(form.resultado),
    titulo: form.titulo.trim(),
    descripcion: form.descripcion.trim(),
    formatos_permitidos: form.formatos_permitidos,
    fecha_limite: form.fecha_limite ? new Date(form.fecha_limite).toISOString() : null,
    permite_tardias: form.permite_tardias,
    rubrica: form.rubrica,
  })

  // Retorna si se guardó (para encadenar "guardar y publicar").
  const guardar = async (): Promise<boolean> => {
    if (guardando) return false
    if (!form.resultado || !form.titulo.trim() || !form.descripcion.trim() || !form.fecha_limite) {
      toast.error('Completa resultado de aprendizaje, título, descripción y fecha límite')
      return false
    }
    setGuardando(true)
    try {
      const res =
        abiertaId === 'nueva'
          ? await api.post<Tarea>('/evaluacion/docente/tareas/', cuerpo())
          : await api.patch<Tarea>(`/evaluacion/docente/tareas/${abiertaId}/`, cuerpo())
      setAbiertaId(res.data.id)
      setForm(formDesde(res.data))
      toast.success('Tarea guardada como borrador')
      recargarTareas()
      return true
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la tarea'))
      return false
    } finally {
      setGuardando(false)
    }
  }

  const publicar = async () => {
    if (typeof abiertaId !== 'number' || publicando) return
    if (!(await guardar())) return
    setPublicando(true)
    try {
      await api.post(`/evaluacion/docente/tareas/${abiertaId}/publicar/`)
      toast.success('Tarea publicada para los estudiantes del curso')
      recargarTareas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo publicar la tarea'))
    } finally {
      setPublicando(false)
    }
  }

  const eliminar = async () => {
    if (typeof abiertaId !== 'number') return
    try {
      await api.delete(`/evaluacion/docente/tareas/${abiertaId}/`)
      toast.success('Borrador eliminado')
      setAbiertaId(null)
      recargarTareas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo eliminar la tarea'))
    }
  }

  const generar = async (datos: { resultado: string; fecha_limite: string; formatos_permitidos: FormatoEntrega[] }) => {
    if (generando) return false
    setGenerando(true)
    try {
      const res = await api.post<Tarea>(
        '/evaluacion/docente/tareas/generar/',
        {
          asignatura: Number(asignaturaId),
          resultado: Number(datos.resultado),
          fecha_limite: new Date(datos.fecha_limite).toISOString(),
          formatos_permitidos: datos.formatos_permitidos,
        },
        { timeout: TIMEOUT_IA },
      )
      toast.success('Borrador generado: revísalo antes de publicar')
      recargarTareas()
      abrir(res.data)
      return true
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo generar la tarea'))
      return false
    } finally {
      setGenerando(false)
    }
  }

  const subirGuia = async (archivo: File) => {
    if (typeof abiertaId !== 'number') {
      toast.error('Guarda el borrador antes de adjuntar archivos guía')
      return
    }
    setSubiendo(true)
    try {
      const datos = new FormData()
      datos.append('archivo', archivo)
      await api.post(`/evaluacion/docente/tareas/${abiertaId}/archivos/`, datos, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })
      toast.success('Archivo guía agregado')
      recargarTareas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo subir el archivo'))
    } finally {
      setSubiendo(false)
    }
  }

  const quitarGuia = async (archivoId: number) => {
    try {
      await api.delete(`/evaluacion/docente/tareas/${abiertaId}/archivos/${archivoId}/`)
      recargarTareas()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo quitar el archivo'))
    }
  }

  const calificar = async (entregaId: number, niveles: number[], observaciones: string) => {
    setGuardandoNota(true)
    try {
      await api.post(`/evaluacion/docente/entregas/${entregaId}/calificar/`, {
        niveles_elegidos: niveles,
        observaciones,
      })
      toast.success('Calificación guardada')
      setCalificando(null)
      setVersionEntregas((n) => n + 1)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la calificación'))
    } finally {
      setGuardandoNota(false)
    }
  }

  // HU-15: propuesta de la IA para una entrega (solo la ve el docente). Reemplaza
  // la fila en el panel y en el diálogo abierto. Devuelve false si falló.
  const reemplazarFila = (fila: FilaEntrega) => {
    setEntregas((actual) => actual.map((f) => (f.estudiante.id === fila.estudiante.id ? fila : f)))
    setCalificando((actual) => (actual && actual.estudiante.id === fila.estudiante.id ? fila : actual))
  }

  const pedirPreevaluacion = async (entregaId: number, avisar: boolean) => {
    try {
      const res = await api.post<FilaEntrega>(`/evaluacion/docente/entregas/${entregaId}/preevaluar/`, {}, {
        timeout: TIMEOUT_IA,
      })
      reemplazarFila(res.data)
      if (avisar) toast.success('Propuesta de la IA lista: revísala antes de calificar')
      return true
    } catch (err: unknown) {
      if (avisar) toast.error(mensajeError(err, 'No se pudo analizar la entrega'))
      return false
    }
  }

  const preevaluar = async (entregaId: number) => {
    setAnalizando([entregaId])
    await pedirPreevaluacion(entregaId, true)
    setAnalizando([])
  }

  // Analiza, una a una, las entregas sin nota ni propuesta (HU-15.1).
  const preevaluarPendientes = async () => {
    const ids = entregas
      .filter((f) => f.entrega && !f.entrega.calificacion && !f.entrega.preevaluacion)
      .map((f) => f.entrega!.id)
    if (!ids.length) return
    setAnalizando(ids)
    setProgresoIA({ hechas: 0, total: ids.length })
    let fallidas = 0
    for (const [i, id] of ids.entries()) {
      if (!(await pedirPreevaluacion(id, false))) fallidas += 1
      setProgresoIA({ hechas: i + 1, total: ids.length })
    }
    setAnalizando([])
    setProgresoIA(null)
    const listas = ids.length - fallidas
    if (listas) toast.success(`${listas} propuesta(s) de la IA listas para revisar`)
    if (fallidas) toast.warning(`${fallidas} entrega(s) no se pudieron analizar: califícalas a mano o inténtalo de nuevo`)
  }

  return {
    asignaturas, asignaturaId, elegirAsignatura, asignatura, cargando, errorCarga,
    tareas, abiertaId, setAbiertaId, abierta, form, setForm,
    nueva, abrir, guardar, guardando, publicar, publicando, eliminar,
    generar, generando, subirGuia, subiendo, quitarGuia,
    entregas, calificando, setCalificando, calificar, guardandoNota,
    preevaluar, preevaluarPendientes, analizando, progresoIA,
  }
}

export type TareasDocente = ReturnType<typeof useTareasDocente>
