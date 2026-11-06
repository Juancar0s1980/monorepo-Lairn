// Hook de la página "Evaluación formal" de un momento (HU-06).
//
// Carga las evaluaciones del momento y el banco elegible (preguntas aprobadas
// de los RA vinculados, ya sin las usadas en laboratorio). Permite crear y
// editar datos (fechas, duración), elegir preguntas y publicar.
// Las reglas viven en el backend; aquí solo se anticipan errores obvios.
// Horario: el formulario guarda fecha, hora, duración y tolerancia; el cierre
// se calcula (inicio + duración + tolerancia) y al editar la tolerancia se deduce.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import type { BancoElegible, EvaluacionFormal, TipoEvaluacion } from '@/types/evaluacion-formal'
import type { PreguntaBanco } from '@/types/banco'
import { mensajeError } from './academico-utils'
import {
  DURACION_PREDETERMINADA,
  TOLERANCIA_PREDETERMINADA,
  componerInicio,
  deducirTolerancia,
  separarInicio,
} from './horario-utils'

// <input type="datetime-local"> trabaja en hora local sin zona; el backend en ISO.
export function aEntradaLocal(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const desfase = d.getTimezoneOffset() * 60000
  return new Date(d.getTime() - desfase).toISOString().slice(0, 16)
}

export const FORM_EVALUACION_VACIO = {
  nombre: '',
  instrucciones: '',
  tipo: 'cuestionario' as TipoEvaluacion,
  // Id de la tarea (solo tipo 'tarea'); '' = sin elegir.
  tarea: '',
  // Fecha (AAAA-MM-DD) y hora (HH:MM) locales de inicio.
  fecha: '',
  hora: '',
  duracion_minutos: DURACION_PREDETERMINADA,
  // Margen para llegar tarde con el tiempo completo; define el cierre.
  tolerancia_minutos: TOLERANCIA_PREDETERMINADA,
}

export type FormEvaluacion = typeof FORM_EVALUACION_VACIO

export function useEvaluacionFormal(momentoId: string) {
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionFormal[]>([])
  const [banco, setBanco] = useState<BancoElegible | null>(null)
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')
  const [version, setVersion] = useState(0)

  // Evaluación abierta en el editor ('nueva' = creando).
  const [seleccionadaId, setSeleccionadaId] = useState<number | 'nueva' | null>(null)
  const [form, setForm] = useState<FormEvaluacion>(FORM_EVALUACION_VACIO)
  const [preguntasElegidas, setPreguntasElegidas] = useState<number[]>([])
  const [guardando, setGuardando] = useState(false)
  const [publicando, setPublicando] = useState(false)

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const [rEval, rBanco] = await Promise.all([
          api.get<EvaluacionFormal[]>(`/evaluacion/momentos/${momentoId}/evaluaciones/`),
          api.get<BancoElegible>(`/evaluacion/momentos/${momentoId}/banco-elegible/`),
        ])
        if (!activo) return
        setEvaluaciones(Array.isArray(rEval.data) ? rEval.data : [])
        setBanco(rBanco.data)
        setErrorCarga('')
      } catch (err: unknown) {
        if (activo) setErrorCarga(mensajeError(err, 'No se pudo cargar el momento de evaluación.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [momentoId, version])

  const recargar = () => setVersion((n) => n + 1)

  const seleccionada = useMemo(
    () => evaluaciones.find((e) => e.id === seleccionadaId) ?? null,
    [evaluaciones, seleccionadaId],
  )
  const soloLectura = seleccionada?.estado === 'publicada'

  // Índice id -> pregunta para mostrar la selección con su texto.
  const preguntasPorId = useMemo(() => {
    const mapa = new Map<number, PreguntaBanco>()
    banco?.resultados.forEach((r) => r.preguntas.forEach((p) => mapa.set(p.id, p)))
    return mapa
  }, [banco])

  const nueva = () => {
    setSeleccionadaId('nueva')
    setForm({ ...FORM_EVALUACION_VACIO })
    setPreguntasElegidas([])
  }

  const abrir = async (e: EvaluacionFormal) => {
    setSeleccionadaId(e.id)
    setForm({
      nombre: e.nombre,
      instrucciones: e.instrucciones,
      tipo: e.tipo,
      tarea: e.tarea ? String(e.tarea) : '',
      ...separarInicio(e.fecha_inicio),
      duracion_minutos: e.duracion_minutos,
      tolerancia_minutos: deducirTolerancia(e.fecha_inicio, e.fecha_fin, e.duracion_minutos),
    })
    try {
      const res = await api.get<PreguntaBanco[]>(`/evaluacion/evaluaciones/${e.id}/preguntas/`)
      setPreguntasElegidas(res.data.map((p) => p.id))
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudieron cargar las preguntas de la evaluación'))
    }
  }

  const alternarPregunta = (id: number) =>
    setPreguntasElegidas((actual) => (actual.includes(id) ? actual.filter((x) => x !== id) : [...actual, id]))

  // Guarda datos + selección (al crear, primero crea y luego fija preguntas).
  // Retorna si se guardó, para encadenar "guardar y publicar".
  const guardar = async (): Promise<boolean> => {
    if (guardando || soloLectura) return false
    const inicio = componerInicio(form.fecha, form.hora)
    if (!form.nombre.trim() || !inicio) {
      toast.error('Completa el nombre, la fecha y la hora de inicio')
      return false
    }
    const fin = new Date(inicio.getTime() + (Number(form.duracion_minutos) + Number(form.tolerancia_minutos)) * 60000)
    setGuardando(true)
    try {
      const datos = {
        nombre: form.nombre.trim(),
        instrucciones: form.instrucciones,
        tipo: form.tipo,
        tarea: form.tipo === 'tarea' && form.tarea ? Number(form.tarea) : null,
        fecha_inicio: inicio.toISOString(),
        fecha_fin: fin.toISOString(),
        duracion_minutos: Number(form.duracion_minutos),
      }
      const res =
        seleccionadaId === 'nueva'
          ? await api.post<EvaluacionFormal>(`/evaluacion/momentos/${momentoId}/evaluaciones/`, datos)
          : await api.patch<EvaluacionFormal>(`/evaluacion/evaluaciones/${seleccionadaId}/`, datos)
      // Una evaluación por tarea no lleva preguntas del banco.
      await api.put(`/evaluacion/evaluaciones/${res.data.id}/preguntas/`, {
        preguntas: form.tipo === 'cuestionario' ? preguntasElegidas : [],
      })
      setSeleccionadaId(res.data.id)
      toast.success('Evaluación guardada como borrador')
      recargar()
      return true
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la evaluación'))
      return false
    } finally {
      setGuardando(false)
    }
  }

  // Publica lo que se ve en pantalla: guarda primero y solo publica si funcionó.
  const publicar = async () => {
    if (typeof seleccionadaId !== 'number' || publicando) return
    if (!(await guardar())) return
    setPublicando(true)
    try {
      await api.post(`/evaluacion/evaluaciones/${seleccionadaId}/publicar/`)
      toast.success('Evaluación publicada')
      recargar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo publicar la evaluación'))
    } finally {
      setPublicando(false)
    }
  }

  return {
    evaluaciones, banco, cargando, errorCarga, recargar,
    seleccionadaId, setSeleccionadaId, seleccionada, soloLectura,
    form, setForm, preguntasElegidas, alternarPregunta, preguntasPorId,
    nueva, abrir, guardar, guardando, publicar, publicando,
  }
}

export type EvaluacionFormalHook = ReturnType<typeof useEvaluacionFormal>
