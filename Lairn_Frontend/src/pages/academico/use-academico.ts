// Hook central del módulo Académico: estado + CRUD de programas, malla,
// competencias, resultados, momentos, vínculos e integración NOVA/cargues.
//
// Por qué existe: pagina-academico.tsx tenía 2000+ líneas con 6 Promise.all
// frágiles (si fallaba el tablero, se caía toda la vista y parecía que el
// CRUD "no hacía nada"). Ahora:
//   - recargarDetalle usa allSettled: cada lista falla por separado.
//   - Tras crear/editar/borrar solo se recarga lo necesario.
//   - Tras crear un programa se selecciona por id devuelto (no por "último").
//   - Se agregan subir PDF y aprobar cargue (existían en backend pero sin UI).

import { useCallback, useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import type {
  AsignaturaMalla,
  CargueDocumental,
  Competencia,
  CorreccionPropuesta,
  MomentoEvaluacion,
  MomentoResultado,
  ProgramaAcademico,
  ResumenImportacion,
  ResultadoAprobacionCargue,
  ResultadoAprendizaje,
  SemestrePrograma,
  TableroPrograma,
} from '@/types/academico'
import {
  FORM_ASIGNATURA_VACIO,
  FORM_MOMENTO_VACIO,
  FORM_PROGRAMA_VACIO,
  FORM_RESULTADO_VACIO,
  mensajeError,
  type ConfirmacionBorrado,
} from './academico-utils'

// Lee una lista del backend sin tumbar al resto si falla.
async function getLista<T>(url: string, nombre: string): Promise<T[]> {
  try {
    const res = await api.get<T[]>(url)
    return Array.isArray(res.data) ? res.data : []
  } catch (err) {
    toast.error(`No se pudo cargar ${nombre}: ${mensajeError(err, 'error de red')}`)
    return []
  }
}

export function useAcademico() {
  // Programas activos (lista base para todos los selects).
  const [programas, setProgramas] = useState<ProgramaAcademico[]>([])
  const [programaId, setProgramaId] = useState<string>('')
  const [busqueda, setBusqueda] = useState('')
  const [cargando, setCargando] = useState(true)
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const [guardando, setGuardando] = useState(false)

  // ---- Programa: crear / editar ----
  const [modalPrograma, setModalPrograma] = useState(false)
  const [editandoPrograma, setEditandoPrograma] = useState<ProgramaAcademico | null>(null)
  const [formPrograma, setFormPrograma] = useState({ ...FORM_PROGRAMA_VACIO })

  // ---- Malla: semestres ----
  const [modalSemestre, setModalSemestre] = useState(false)
  const [editandoSemestre, setEditandoSemestre] = useState<SemestrePrograma | null>(null)
  const [formSemestre, setFormSemestre] = useState({ numero: 1, nombre: '' })

  // ---- Malla: asignaturas ----
  const [modalAsignatura, setModalAsignatura] = useState(false)
  const [editandoAsignatura, setEditandoAsignatura] = useState<AsignaturaMalla | null>(null)
  const [formAsignatura, setFormAsignatura] = useState({ ...FORM_ASIGNATURA_VACIO })

  // ---- Competencias ----
  const [modalCompetencia, setModalCompetencia] = useState(false)
  const [editandoCompetencia, setEditandoCompetencia] = useState<Competencia | null>(null)
  const [formCompetencia, setFormCompetencia] = useState({
    nombre: '',
    tipo: 'especifica' as 'transversal' | 'especifica',
    descripcion: '',
  })

  // ---- Resultados DCE ----
  const [modalResultado, setModalResultado] = useState(false)
  const [editandoResultado, setEditandoResultado] = useState<ResultadoAprendizaje | null>(null)
  const [formResultado, setFormResultado] = useState({ ...FORM_RESULTADO_VACIO })

  // ---- Momentos ----
  const [modalMomento, setModalMomento] = useState(false)
  const [editandoMomento, setEditandoMomento] = useState<MomentoEvaluacion | null>(null)
  const [formMomento, setFormMomento] = useState({ ...FORM_MOMENTO_VACIO })

  // ---- Vínculos momento -> RA ----
  const [momentoVinculando, setMomentoVinculando] = useState<MomentoEvaluacion | null>(null)
  const [vinculosMomento, setVinculosMomento] = useState<MomentoResultado[]>([])
  const [cargandoVinculos, setCargandoVinculos] = useState(false)
  const [formVinculo, setFormVinculo] = useState({ resultado: '', obligatorio: true })

  // ---- Confirmación de borrado ----
  const [confirmacion, setConfirmacion] = useState<ConfirmacionBorrado | null>(null)
  const [eliminando, setEliminando] = useState(false)

  // Datos por pestaña (se recargan al cambiar de programa).
  const [semestres, setSemestres] = useState<SemestrePrograma[]>([])
  const [asignaturas, setAsignaturas] = useState<AsignaturaMalla[]>([])
  const [competencias, setCompetencias] = useState<Competencia[]>([])
  const [resultados, setResultados] = useState<ResultadoAprendizaje[]>([])
  const [momentos, setMomentos] = useState<MomentoEvaluacion[]>([])
  const [tablero, setTablero] = useState<TableroPrograma | null>(null)
  const [cargues, setCargues] = useState<CargueDocumental[]>([])

  // Importación JSON NOVA.
  const [jsonNOVA, setJsonNOVA] = useState('')
  const [modoImportacion, setModoImportacion] = useState<'simulacro' | 'real'>('simulacro')
  const [importando, setImportando] = useState(false)
  const [resumenImportacion, setResumenImportacion] = useState<ResumenImportacion | null>(null)

  // Subida de PDF (pensum / resolución / plan de aula).
  const [subiendoPdf, setSubiendoPdf] = useState(false)
  const [tipoPdf, setTipoPdf] = useState<'pensum' | 'resolucion' | 'plan_aula'>('pensum')
  const [aprobandoCargue, setAprobandoCargue] = useState<number | null>(null)
  // Cargue abierto en el diálogo de revisión previa a aprobar.
  const [revisandoCargue, setRevisandoCargue] = useState<CargueDocumental | null>(null)

  // Recarga el detalle completo del programa activo (malla, DCE, momentos).
  // Usa allSettled: si el tablero falla, igual se muestran las listas.
  const recargarDetalle = useCallback(async (id: string) => {
    if (!id) return
    setCargandoDetalle(true)
    const base = `/evaluacion/programas/${id}`
    const [rSem, rAsig, rComp, rRA, rMom, rTab] = await Promise.allSettled([
      api.get<SemestrePrograma[]>(`${base}/semestres/`),
      api.get<AsignaturaMalla[]>(`${base}/asignaturas/`),
      api.get<Competencia[]>(`${base}/competencias/`),
      api.get<ResultadoAprendizaje[]>(`${base}/resultados/`),
      api.get<MomentoEvaluacion[]>(`${base}/momentos/`),
      api.get<TableroPrograma>(`${base}/tablero/`),
    ])
    if (rSem.status === 'fulfilled') setSemestres(Array.isArray(rSem.value.data) ? rSem.value.data : [])
    else toast.error('No se pudieron cargar los semestres')
    if (rAsig.status === 'fulfilled') setAsignaturas(Array.isArray(rAsig.value.data) ? rAsig.value.data : [])
    else toast.error('No se pudieron cargar las asignaturas')
    if (rComp.status === 'fulfilled') setCompetencias(Array.isArray(rComp.value.data) ? rComp.value.data : [])
    else toast.error('No se pudieron cargar las competencias')
    if (rRA.status === 'fulfilled') setResultados(Array.isArray(rRA.value.data) ? rRA.value.data : [])
    else toast.error('No se pudieron cargar los resultados')
    if (rMom.status === 'fulfilled') setMomentos(Array.isArray(rMom.value.data) ? rMom.value.data : [])
    else toast.error('No se pudieron cargar los momentos')
    if (rTab.status === 'fulfilled') setTablero(rTab.value.data)
    else setTablero(null)
    setCargandoDetalle(false)
  }, [])

  // Recarga la lista de programas preservando la selección actual.
  const recargarProgramas = useCallback(async (preservarId?: string) => {
    const lista = await getLista<ProgramaAcademico>('/evaluacion/programas/', 'los programas')
    setProgramas(lista)
    if (lista.length === 0) {
      setProgramaId('')
      return lista
    }
    const objetivo = preservarId ?? programaId
    if (objetivo && lista.some((p) => String(p.id) === String(objetivo))) {
      setProgramaId(String(objetivo))
    } else if (!programaId || !lista.some((p) => String(p.id) === String(programaId))) {
      // Solo cambia la selección si la actual ya no existe.
      setProgramaId((actual) =>
        actual && lista.some((p) => String(p.id) === actual) ? actual : String(lista[0].id),
      )
    }
    return lista
  }, [programaId])

  const recargarCargues = useCallback(async () => {
    setCargues(await getLista<CargueDocumental>('/evaluacion/cargues/', 'los cargues'))
  }, [])

  // Carga inicial: programas + cargues.
  useEffect(() => {
    const cargar = async () => {
      try {
        const [resProgramas, resCargues] = await Promise.all([
          api.get<ProgramaAcademico[]>('/evaluacion/programas/'),
          api.get<CargueDocumental[]>('/evaluacion/cargues/'),
        ])
        const lista = Array.isArray(resProgramas.data) ? resProgramas.data : []
        setProgramas(lista)
        setCargues(Array.isArray(resCargues.data) ? resCargues.data : [])
        if (lista.length > 0) setProgramaId(String(lista[0].id))
      } catch {
        toast.error('No se pudieron cargar los programas')
      } finally {
        setCargando(false)
      }
    }
    cargar()
  }, [])

  // Al cambiar de programa: semestres, malla, DCE, momentos y tablero.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!programaId) return
    void recargarDetalle(programaId)
  }, [programaId, recargarDetalle])

  // Filtro de búsqueda en cliente (las listas son pequeñas).
  const programasFiltrados = useMemo(() => {
    const t = busqueda.trim().toLowerCase()
    if (!t) return programas
    return programas.filter(
      (p) => p.nombre.toLowerCase().includes(t) || p.codigo.toLowerCase().includes(t),
    )
  }, [programas, busqueda])

  // Nombre del semestre para mostrar la asignatura ubicada.
  const nombreSemestre = useCallback(
    (a: AsignaturaMalla): string => {
      if (a.semestre_numero != null) return `S${a.semestre_numero}`
      if (a.semestre == null) return 'Sin ubicar'
      const s = semestres.find((x) => x.id === a.semestre)
      return s ? `S${s.numero}` : `S${a.semestre}`
    },
    [semestres],
  )

  // ============ PROGRAMAS: crear / editar ============
  const abrirCrearPrograma = () => {
    setEditandoPrograma(null)
    setFormPrograma({ ...FORM_PROGRAMA_VACIO })
    setModalPrograma(true)
  }

  const abrirEditarPrograma = (p: ProgramaAcademico) => {
    setEditandoPrograma(p)
    setFormPrograma({
      codigo: p.codigo,
      nombre: p.nombre,
      modalidad: p.modalidad,
      sede: p.sede,
      duracion_semestres: p.duracion_semestres,
      fecha_vigencia: p.fecha_vigencia ?? '',
    })
    setModalPrograma(true)
  }

  const guardarPrograma = async () => {
    if (!formPrograma.codigo.trim() || !formPrograma.nombre.trim()) {
      toast.error('Código y nombre son obligatorios')
      return
    }
    setGuardando(true)
    try {
      const payload = {
        codigo: formPrograma.codigo.trim(),
        nombre: formPrograma.nombre.trim(),
        modalidad: formPrograma.modalidad,
        sede: formPrograma.sede,
        duracion_semestres: Number(formPrograma.duracion_semestres),
        fecha_vigencia: formPrograma.fecha_vigencia || null,
      }
      if (editandoPrograma) {
        await api.patch(`/evaluacion/programas/${editandoPrograma.id}/`, payload)
        toast.success('Programa actualizado')
        setModalPrograma(false)
        await recargarProgramas(String(editandoPrograma.id))
        await recargarDetalle(String(editandoPrograma.id))
      } else {
        const res = await api.post<ProgramaAcademico>('/evaluacion/programas/', payload)
        toast.success('Programa creado')
        setModalPrograma(false)
        const nuevoId = String(res.data?.id ?? '')
        const lista = await recargarProgramas(nuevoId || undefined)
        // Selecciona el programa recién creado por id (no por "último").
        if (nuevoId && lista.some((p) => String(p.id) === nuevoId)) setProgramaId(nuevoId)
      }
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar el programa'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ SEMESTRES: crear / editar ============
  const abrirCrearSemestre = () => {
    const siguiente = semestres.length > 0 ? Math.max(...semestres.map((s) => s.numero)) + 1 : 1
    setEditandoSemestre(null)
    setFormSemestre({ numero: siguiente, nombre: '' })
    setModalSemestre(true)
  }

  const abrirEditarSemestre = (s: SemestrePrograma) => {
    setEditandoSemestre(s)
    setFormSemestre({ numero: s.numero, nombre: s.nombre ?? '' })
    setModalSemestre(true)
  }

  const guardarSemestre = async () => {
    if (!programaId) {
      toast.error('Selecciona un programa primero')
      return
    }
    if (!formSemestre.numero || formSemestre.numero < 1) {
      toast.error('El número de semestre debe ser mayor a 0')
      return
    }
    setGuardando(true)
    try {
      if (editandoSemestre) {
        await api.patch(
          `/evaluacion/programas/${programaId}/semestres/${editandoSemestre.id}/`,
          formSemestre,
        )
        toast.success('Semestre actualizado')
      } else {
        await api.post(`/evaluacion/programas/${programaId}/semestres/`, formSemestre)
        toast.success('Semestre creado')
      }
      setModalSemestre(false)
      await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar el semestre'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ ASIGNATURAS: crear / editar ============
  const abrirCrearAsignatura = () => {
    setEditandoAsignatura(null)
    setFormAsignatura({ ...FORM_ASIGNATURA_VACIO })
    setModalAsignatura(true)
  }

  const abrirEditarAsignatura = (a: AsignaturaMalla) => {
    setEditandoAsignatura(a)
    setFormAsignatura({
      codigo: a.codigo,
      nombre: a.nombre,
      creditos: a.creditos,
      intensidad_horaria: a.intensidad_horaria,
      tipo: a.tipo,
      semestre: a.semestre != null ? String(a.semestre) : '',
    })
    setModalAsignatura(true)
  }

  const guardarAsignatura = async () => {
    if (!programaId) {
      toast.error('Selecciona un programa primero')
      return
    }
    if (!formAsignatura.codigo.trim() || !formAsignatura.nombre.trim()) {
      toast.error('Código y nombre son obligatorios')
      return
    }
    setGuardando(true)
    try {
      const semestreId =
        formAsignatura.semestre && formAsignatura.semestre !== 'sin-ubicar'
          ? Number(formAsignatura.semestre)
          : null
      const payload = {
        codigo: formAsignatura.codigo.trim(),
        nombre: formAsignatura.nombre.trim(),
        creditos: Number(formAsignatura.creditos),
        intensidad_horaria: Number(formAsignatura.intensidad_horaria),
        tipo: formAsignatura.tipo,
        // El backend espera el id del semestre o null si aún no se ubica.
        semestre: semestreId,
      }
      if (editandoAsignatura) {
        await api.patch(
          `/evaluacion/programas/${programaId}/asignaturas/${editandoAsignatura.id}/`,
          payload,
        )
        toast.success('Asignatura actualizada')
      } else {
        await api.post(`/evaluacion/programas/${programaId}/asignaturas/`, payload)
        toast.success('Asignatura creada')
      }
      setModalAsignatura(false)
      await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la asignatura'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ COMPETENCIAS: crear / editar ============
  const abrirCrearCompetencia = () => {
    setEditandoCompetencia(null)
    setFormCompetencia({ nombre: '', tipo: 'especifica', descripcion: '' })
    setModalCompetencia(true)
  }

  const abrirEditarCompetencia = (c: Competencia) => {
    setEditandoCompetencia(c)
    setFormCompetencia({ nombre: c.nombre, tipo: c.tipo, descripcion: c.descripcion ?? '' })
    setModalCompetencia(true)
  }

  const guardarCompetencia = async () => {
    if (!programaId) {
      toast.error('Selecciona un programa primero')
      return
    }
    if (!formCompetencia.nombre.trim()) {
      toast.error('El nombre de la competencia es obligatorio')
      return
    }
    setGuardando(true)
    try {
      const payload = {
        nombre: formCompetencia.nombre.trim(),
        tipo: formCompetencia.tipo,
        descripcion: formCompetencia.descripcion.trim(),
      }
      if (editandoCompetencia) {
        await api.patch(`/evaluacion/competencias/${editandoCompetencia.id}/`, payload)
        toast.success('Competencia actualizada')
      } else {
        await api.post(`/evaluacion/programas/${programaId}/competencias/`, payload)
        toast.success('Competencia creada')
      }
      setModalCompetencia(false)
      await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la competencia'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ RESULTADOS DCE: crear / editar ============
  const abrirCrearResultado = () => {
    setEditandoResultado(null)
    setFormResultado({ ...FORM_RESULTADO_VACIO })
    setModalResultado(true)
  }

  const abrirEditarResultado = (ra: ResultadoAprendizaje) => {
    setEditandoResultado(ra)
    setFormResultado({
      competencia: String(ra.competencia),
      asignatura: String(ra.asignatura),
      descripcion: ra.descripcion,
      evidencia_observable: ra.evidencia_observable ?? '',
      tarea_sugerida: ra.tarea_sugerida ?? '',
    })
    setModalResultado(true)
  }

  const guardarResultado = async () => {
    if (!programaId) {
      toast.error('Selecciona un programa primero')
      return
    }
    if (!formResultado.competencia || !formResultado.asignatura) {
      toast.error('Competencia y asignatura son obligatorias')
      return
    }
    if (!formResultado.descripcion.trim()) {
      toast.error('La descripción (afirmación DCE) es obligatoria')
      return
    }
    setGuardando(true)
    try {
      const payload = {
        competencia: Number(formResultado.competencia),
        asignatura: Number(formResultado.asignatura),
        descripcion: formResultado.descripcion.trim(),
        evidencia_observable: formResultado.evidencia_observable.trim(),
        tarea_sugerida: formResultado.tarea_sugerida.trim(),
      }
      if (editandoResultado) {
        const res = await api.patch(`/evaluacion/resultados/${editandoResultado.id}/`, payload)
        const versionado = (res.data as { versionado?: boolean } | undefined)?.versionado
        toast.success(
          versionado
            ? 'Resultado versionado (el anterior quedó como histórico)'
            : 'Resultado actualizado',
        )
      } else {
        await api.post(`/evaluacion/programas/${programaId}/resultados/`, payload)
        toast.success('Resultado de aprendizaje creado')
      }
      setModalResultado(false)
      await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar el resultado'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ MOMENTOS: crear / editar ============
  const abrirCrearMomento = () => {
    setEditandoMomento(null)
    setFormMomento({ ...FORM_MOMENTO_VACIO, nombre: `Momento ${momentos.length + 1}` })
    setModalMomento(true)
  }

  const abrirEditarMomento = (m: MomentoEvaluacion) => {
    setEditandoMomento(m)
    setFormMomento({
      semestre_referencia: m.semestre_referencia,
      nombre: m.nombre,
      periodo: m.periodo ?? '',
      descripcion: m.descripcion ?? '',
    })
    setModalMomento(true)
  }

  const guardarMomento = async () => {
    if (!programaId) {
      toast.error('Selecciona un programa primero')
      return
    }
    if (!formMomento.nombre.trim()) {
      toast.error('El nombre del momento es obligatorio')
      return
    }
    setGuardando(true)
    try {
      const payload = {
        semestre_referencia: Number(formMomento.semestre_referencia),
        nombre: formMomento.nombre.trim(),
        periodo: formMomento.periodo.trim(),
        descripcion: formMomento.descripcion.trim(),
      }
      if (editandoMomento) {
        await api.patch(`/evaluacion/momentos/${editandoMomento.id}/`, payload)
        toast.success('Momento actualizado')
      } else {
        await api.post(`/evaluacion/programas/${programaId}/momentos/`, payload)
        toast.success('Momento creado')
      }
      setModalMomento(false)
      await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar el momento'))
    } finally {
      setGuardando(false)
    }
  }

  // ============ VÍNCULOS momento -> RA ============
  const abrirVinculos = async (m: MomentoEvaluacion) => {
    setMomentoVinculando(m)
    setFormVinculo({ resultado: '', obligatorio: true })
    setCargandoVinculos(true)
    try {
      const res = await api.get<MomentoResultado[]>(`/evaluacion/momentos/${m.id}/vinculos/`)
      setVinculosMomento(Array.isArray(res.data) ? res.data : [])
    } catch {
      toast.error('No se pudieron cargar los vínculos del momento')
      setVinculosMomento([])
    } finally {
      setCargandoVinculos(false)
    }
  }

  const crearVinculo = async () => {
    if (!momentoVinculando) return
    if (!formVinculo.resultado) {
      toast.error('Selecciona un resultado de aprendizaje')
      return
    }
    setGuardando(true)
    try {
      await api.post(`/evaluacion/momentos/${momentoVinculando.id}/vinculos/`, {
        resultado: Number(formVinculo.resultado),
        obligatorio: formVinculo.obligatorio,
      })
      toast.success('Resultado vinculado al momento')
      const res = await api.get<MomentoResultado[]>(
        `/evaluacion/momentos/${momentoVinculando.id}/vinculos/`,
      )
      setVinculosMomento(Array.isArray(res.data) ? res.data : [])
      setFormVinculo({ resultado: '', obligatorio: true })
      if (programaId) await recargarDetalle(programaId)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo vincular (¿ya estaba vinculado?)'))
    } finally {
      setGuardando(false)
    }
  }

  const recargarVinculos = async (momentoId: number) => {
    const res = await api.get<MomentoResultado[]>(`/evaluacion/momentos/${momentoId}/vinculos/`)
    setVinculosMomento(Array.isArray(res.data) ? res.data : [])
  }

  // Ejecuta el borrado (lógico en casi todo; físico solo en vínculos).
  const ejecutarBorrado = async () => {
    if (!confirmacion) return
    setEliminando(true)
    try {
      switch (confirmacion.tipo) {
        case 'programa': {
          // Borrado lógico en cascada: el backend desactiva malla, DCE y
          // momentos, elimina cargues pendientes y devuelve el conteo.
          const res = await api.delete<{
            desactivados?: Record<string, number>
            cargues_eliminados?: number
          }>(`/evaluacion/programas/${confirmacion.id}/`)
          const d = res.data.desactivados ?? {}
          const total = Object.values(d).reduce((a, b) => a + (b || 0), 0)
          const cargues = res.data.cargues_eliminados ?? 0
          toast.success(
            `Programa desactivado: ${total} registros al histórico` +
              (cargues > 0 ? `, ${cargues} cargues pendientes eliminados` : ''),
          )
          break
        }
        case 'semestre':
          await api.delete(`/evaluacion/programas/${programaId}/semestres/${confirmacion.id}/`)
          toast.success('Semestre eliminado')
          break
        case 'asignatura':
          await api.delete(`/evaluacion/programas/${programaId}/asignaturas/${confirmacion.id}/`)
          toast.success('Asignatura eliminada')
          break
        case 'competencia':
          await api.delete(`/evaluacion/competencias/${confirmacion.id}/`)
          toast.success('Competencia eliminada')
          break
        case 'resultado':
          await api.delete(`/evaluacion/resultados/${confirmacion.id}/`)
          toast.success('Resultado eliminado')
          break
        case 'momento':
          await api.delete(`/evaluacion/momentos/${confirmacion.id}/`)
          toast.success('Momento eliminado')
          break
        case 'vinculo':
          await api.delete(`/evaluacion/vinculos/${confirmacion.id}/`)
          toast.success('Vínculo eliminado')
          if (momentoVinculando) await recargarVinculos(momentoVinculando.id)
          break
        case 'cargue':
          // Borrado físico: el PDF nunca se guardó; el backend bloquea
          // borrar aprobados (auditoría: ya viven en el programa).
          await api.delete(`/evaluacion/cargues/${confirmacion.id}/`)
          toast.success('Cargue eliminado')
          if (revisandoCargue?.id === confirmacion.id) setRevisandoCargue(null)
          break
      }
      setConfirmacion(null)
      // Solo recarga lo necesario: programas solo si cambió la lista base.
      if (confirmacion.tipo === 'programa') {
        const lista = await recargarProgramas()
        if (lista.length > 0) {
          setProgramaId(String(lista[0].id))
          await recargarDetalle(String(lista[0].id))
        } else {
          setProgramaId('')
          setSemestres([])
          setAsignaturas([])
          setCompetencias([])
          setResultados([])
          setMomentos([])
          setTablero(null)
        }
      } else if (confirmacion.tipo === 'cargue') {
        await recargarCargues()
      } else if (confirmacion.tipo !== 'vinculo' && programaId) {
        await recargarDetalle(programaId)
      } else if (confirmacion.tipo === 'vinculo' && programaId) {
        await recargarDetalle(programaId)
      }
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo eliminar'))
    } finally {
      setEliminando(false)
    }
  }

  // Importa JSON NOVA (simulacro no escribe nada).
  const importarNOVA = async () => {
    if (!jsonNOVA.trim()) {
      toast.error('Pega el JSON a importar')
      return
    }
    let datos: unknown
    try {
      datos = JSON.parse(jsonNOVA)
    } catch {
      toast.error('JSON inválido: revisa la sintaxis')
      return
    }
    setImportando(true)
    setResumenImportacion(null)
    try {
      const res = await api.post<ResumenImportacion>('/evaluacion/integracion/importar-json/', {
        datos,
        modo: modoImportacion,
      })
      setResumenImportacion(res.data)
      toast.success(
        res.data.modo === 'simulacro'
          ? `Simulacro: ${res.data.creados} se crearían`
          : `Importado: ${res.data.creados} creados, ${res.data.actualizados} actualizados`,
      )
      if (res.data.modo === 'real') {
        await recargarProgramas(programaId || undefined)
        if (programaId) await recargarDetalle(programaId)
      }
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo importar el JSON'))
    } finally {
      setImportando(false)
    }
  }

  // Sube un PDF de pensum/resolución/plan de aula para propuesta IA.
  const subirPdf = async (archivo: File | null) => {
    if (!archivo) {
      toast.error('Selecciona un PDF primero')
      return
    }
    setSubiendoPdf(true)
    try {
      const form = new FormData()
      form.append('archivo', archivo)
      form.append('tipo', tipoPdf)
      if (programaId) form.append('programa_id', programaId)
      await api.post('/evaluacion/cargues/subir/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        // La extracción IA tarda 30-90s; el timeout global de 15s la mataba
        // y parecía que "no se pudo subir" aunque el backend seguía procesando.
        timeout: 120000,
      })
      toast.success('Documento procesado por IA (revisa la propuesta)')
      await recargarCargues()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo subir el PDF'))
    } finally {
      setSubiendoPdf(false)
    }
  }

  // Actualiza un cargue (programa destino y/o estado procesado<->rechazado).
  // Los aprobados y fallidos son inmutables (los bloquea el backend).
  const actualizarCargue = async (
    cargueId: number,
    cambios: { programa_id?: string | null; estado?: 'procesado' | 'rechazado' },
  ) => {
    setGuardando(true)
    try {
      const body: Record<string, unknown> = {}
      if ('programa_id' in cambios) {
        body.programa_id = cambios.programa_id ? Number(cambios.programa_id) : null
      }
      if (cambios.estado) body.estado = cambios.estado
      const res = await api.patch<CargueDocumental>(
        `/evaluacion/cargues/${cargueId}/`,
        body,
      )
      toast.success(
        cambios.estado === 'rechazado'
          ? 'Propuesta descartada (puedes reabrirla cuando quieras)'
          : cambios.estado === 'procesado'
            ? 'Propuesta reabierta para revisión'
            : 'Cargue actualizado',
      )
      setRevisandoCargue(res.data)
      await recargarCargues()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo actualizar el cargue'))
    } finally {
      setGuardando(false)
    }
  }

  // Aprueba un cargue: primero se revisa la propuesta en el diálogo,
  // luego se incorpora al programa (y a la asignatura si es plan de aula).
  // Acepta correcciones por fila (p. ej. códigos que la IA no extrajo) y
  // la orden de crear el programa desde la resolución.
  const aprobarCargue = async (
    cargueId: number,
    programaDestino?: string,
    asignaturaDestino?: string,
    extras?: { correcciones?: CorreccionPropuesta[]; crearPrograma?: boolean },
  ) => {
    setAprobandoCargue(cargueId)
    try {
      const body: Record<string, unknown> = {}
      if (programaDestino) body.programa_id = Number(programaDestino)
      if (asignaturaDestino) body.asignatura_id = Number(asignaturaDestino)
      if (extras?.correcciones?.length) body.correcciones = extras.correcciones
      if (extras?.crearPrograma) body.crear_programa = true
      const res = await api.post<ResultadoAprobacionCargue>(
        `/evaluacion/cargues/${cargueId}/aprobar/`,
        body,
      )
      const d = res.data.detalle
      const partes = [
        d.asignaturas > 0 ? `${d.asignaturas} asignaturas` : '',
        d.momentos > 0 ? `${d.momentos} momentos` : '',
        d.resultados > 0 ? `${d.resultados} resultados` : '',
        d.competencias > 0 ? `${d.competencias} competencias` : '',
      ].filter(Boolean)
      toast.success(
        partes.length > 0
          ? `Cargue aprobado: ${partes.join(', ')} al programa`
          : 'Cargue aprobado (sin registros nuevos que incorporar)',
      )
      if (res.data.errores.length > 0) {
        toast.error(`Omitidos: ${res.data.errores.slice(0, 3).join(' · ')}`)
      }
      setRevisandoCargue(null)
      await recargarCargues()
      // El programa destino pudo elegirse (o crearse) en la revisión: el
      // backend devuelve su id y se selecciona para mostrar lo incorporado.
      // Se recargan programas (conteos) + detalle (malla, DCE, momentos,
      // tablero) para que todas las pestañas muestren lo incorporado.
      const destinoFinal = String(res.data.programa_id ?? programaDestino ?? programaId ?? '')
      if (destinoFinal && destinoFinal !== programaId) {
        setProgramaId(destinoFinal)
      }
      await recargarProgramas(destinoFinal || undefined)
      if (destinoFinal) await recargarDetalle(destinoFinal)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo aprobar el cargue'))
    } finally {
      setAprobandoCargue(null)
    }
  }

  return {
    // Listas base
    programas, programaId, setProgramaId, busqueda, setBusqueda, programasFiltrados,
    cargando, cargandoDetalle, guardando,
    // Detalle
    semestres, asignaturas, competencias, resultados, momentos, tablero, cargues,
    nombreSemestre, recargarDetalle,
    // Programa
    modalPrograma, setModalPrograma, editandoPrograma, formPrograma, setFormPrograma,
    abrirCrearPrograma, abrirEditarPrograma, guardarPrograma,
    // Semestre
    modalSemestre, setModalSemestre, editandoSemestre, formSemestre, setFormSemestre,
    abrirCrearSemestre, abrirEditarSemestre, guardarSemestre,
    // Asignatura
    modalAsignatura, setModalAsignatura, editandoAsignatura, formAsignatura, setFormAsignatura,
    abrirCrearAsignatura, abrirEditarAsignatura, guardarAsignatura,
    // Competencia
    modalCompetencia, setModalCompetencia, editandoCompetencia, formCompetencia, setFormCompetencia,
    abrirCrearCompetencia, abrirEditarCompetencia, guardarCompetencia,
    // Resultado
    modalResultado, setModalResultado, editandoResultado, formResultado, setFormResultado,
    abrirCrearResultado, abrirEditarResultado, guardarResultado,
    // Momento
    modalMomento, setModalMomento, editandoMomento, formMomento, setFormMomento,
    abrirCrearMomento, abrirEditarMomento, guardarMomento,
    // Vínculos
    momentoVinculando, setMomentoVinculando, vinculosMomento, cargandoVinculos,
    formVinculo, setFormVinculo, abrirVinculos, crearVinculo,
    // Borrado
    confirmacion, setConfirmacion, eliminando, ejecutarBorrado,
    // Integración
    jsonNOVA, setJsonNOVA, modoImportacion, setModoImportacion,
    importando, resumenImportacion, importarNOVA,
    subiendoPdf, tipoPdf, setTipoPdf, subirPdf,
    aprobandoCargue, aprobarCargue, actualizarCargue,
    revisandoCargue, setRevisandoCargue,
  }
}

export type Academico = ReturnType<typeof useAcademico>
