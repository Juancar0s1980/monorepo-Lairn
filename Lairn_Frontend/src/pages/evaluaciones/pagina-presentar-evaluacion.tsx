// Presentación de una evaluación formal (HU-07.2 / 07.3).
//
// - Antes de empezar: instrucciones y advertencias (un solo intento; el
//   tiempo corre aunque se cierre la página).
// - En curso: temporizador sincronizado con el reloj del servidor, cada
//   respuesta se guarda en el servidor al marcarla (con indicador y reintento).
// - Supervisión en sala (ADR-009): si la evaluación exige llamado a lista y el
//   docente aún no te marcó presente o tarde, se muestra el aviso de espera en
//   lugar de "Comenzar" y se vuelve a consultar cada 10 s. Llegar tarde no
//   reduce la duración, pero el intento nunca pasa del cierre de la ventana.
// - Integridad (ADR-010), solo con el intento en curso: se bloquea copiar,
//   pegar, menú contextual, selección y atajos; se detecta cambio de pestaña o
//   ventana y salida de pantalla completa (`use-integridad.ts`). El servidor
//   decide: 1.ª vez advertencia, 2.ª suspensión (tiempo congelado, sin
//   preguntas, re-consulta cada 10 s hasta que el docente reactive o anule).
// - Navegación (ADR-014): índice de preguntas (respondidas / pendientes), barra
//   de progreso, "siguiente pendiente", confirmación antes de enviar y aviso
//   al salir. El aviso del navegador al recargar abre una gracia de 1,5 s para
//   que su propio diálogo no cuente como cambio de ventana (ADR-010).
// - Al llegar a 0 se envía sola; si el navegador estaba cerrado, el servidor
//   ya la habrá cerrado con lo registrado. Recargar la página retoma el intento.

import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '@/services/api'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { AlertTriangle, ArrowLeft, Ban, Check, CheckCircle2, Clock, Hourglass, Loader2, Maximize, PauseCircle, RotateCcw, Send, ShieldAlert, UserX } from 'lucide-react'
import { cn } from '@/lib/utils'
import { bloqueoPorAsistencia, type DetalleEvaluacionEstudiante } from '@/types/presentacion'
import { mensajeError } from '@/pages/academico/academico-utils'
import { pedirPantallaCompleta, useIntegridad, type RespuestaIncidente } from './use-integridad'

type EstadoGuardado = 'guardando' | 'guardada' | 'error'
const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

function reloj(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const dos = (n: number) => String(n).padStart(2, '0')
  return h ? `${h}:${dos(m)}:${dos(s)}` : `${dos(m)}:${dos(s)}`
}

export default function PaginaPresentarEvaluacion() {
  const { evaluacionId = '' } = useParams()
  const navegar = useNavigate()
  const [detalle, setDetalle] = useState<DetalleEvaluacionEstudiante | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  const [respuestas, setRespuestas] = useState<Record<string, number>>({})
  const [guardado, setGuardado] = useState<Record<string, EstadoGuardado>>({})
  // Diferencia reloj servidor - navegador, para que el temporizador no dependa de la hora local.
  const [desfase, setDesfase] = useState(0)
  const [ahora, setAhora] = useState(() => Date.now())
  const [iniciando, setIniciando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [confirmar, setConfirmar] = useState<'iniciar' | 'enviar' | 'salir' | null>(null)
  const autoEnviado = useRef(false)
  // Integridad: aviso de la advertencia y si el navegador rechazó la pantalla completa.
  const [aviso, setAviso] = useState<string | null>(null)
  const pantallaRechazada = useRef(false)
  const [enPantallaCompleta, setEnPantallaCompleta] = useState(() => !!document.fullscreenElement)

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<DetalleEvaluacionEstudiante>(`/evaluacion/estudiante/evaluaciones/${evaluacionId}/`)
        if (!activo) return
        setDetalle(res.data)
        setRespuestas(res.data.respuestas ?? {})
        setDesfase(new Date(res.data.ahora_servidor).getTime() - Date.now())
        setAhora(Date.now())
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se encontró la evaluación.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [evaluacionId, version])

  const integridad = detalle?.intento?.integridad ?? 'normal'
  const suspendido = detalle?.intento?.estado === 'en_curso' && integridad === 'suspendido'
  const anulado = integridad === 'anulado_fraude'
  // "En curso" para el estudiante = puede responder (no suspendido).
  const enCurso = detalle?.intento?.estado === 'en_curso' && !suspendido

  const alResponderIncidente = (r: RespuestaIncidente) => {
    if (r.consecuencia === 'advertencia' && r.aviso) setAviso(r.aviso)
    if (r.integridad === 'suspendido') {
      toast.error(r.aviso ?? 'Evaluación suspendida: espera la decisión del docente.')
      setVersion((n) => n + 1)
    }
  }
  const { reportar, marcarCambioPantalla } = useIntegridad({
    evaluacionId,
    activo: enCurso,
    alResponder: alResponderIncidente,
  })

  useEffect(() => {
    const alCambiar = () => setEnPantallaCompleta(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', alCambiar)
    return () => document.removeEventListener('fullscreenchange', alCambiar)
  }, [])

  // Si el navegador no permitió pantalla completa, se registra (informativo, no cuenta).
  useEffect(() => {
    if (enCurso && pantallaRechazada.current) {
      pantallaRechazada.current = false
      void reportar('pantalla_completa_no_disponible', 'El navegador rechazó la pantalla completa')
    }
  }, [enCurso, reportar])

  // Suspendido: re-consulta cada 10 s para retomar en cuanto el docente decida.
  useEffect(() => {
    if (!suspendido) return
    const id = window.setInterval(() => setVersion((n) => n + 1), 10_000)
    return () => window.clearInterval(id)
  }, [suspendido])

  // Aviso del navegador al cerrar o recargar con el intento en curso.
  useEffect(() => {
    if (!enCurso) return
    const alSalir = (e: BeforeUnloadEvent) => {
      marcarCambioPantalla()
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', alSalir)
    return () => window.removeEventListener('beforeunload', alSalir)
  }, [enCurso, marcarCambioPantalla])

  const irAPregunta = (id: number) =>
    document.getElementById(`pregunta-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  const volverAPantallaCompleta = async () => {
    marcarCambioPantalla()
    if (!(await pedirPantallaCompleta())) toast.info('Tu navegador no permite pantalla completa en este momento.')
  }
  const bloqueo = detalle && detalle.tipo === 'cuestionario' ? bloqueoPorAsistencia(detalle) : null
  const esperandoLlamado = bloqueo === 'Esperando llamado a lista'

  // Mientras espera el llamado a lista, re-consulta cada 10 s para habilitar "Comenzar" sola.
  useEffect(() => {
    if (!bloqueo) return
    const id = window.setInterval(() => setVersion((n) => n + 1), 10_000)
    return () => window.clearInterval(id)
  }, [bloqueo])
  const venceEn = detalle?.intento ? new Date(detalle.intento.vence_en).getTime() : 0
  const restante = venceEn - (ahora + desfase)

  const enviar = async (automatico: boolean) => {
    setEnviando(true)
    try {
      await api.post(`/evaluacion/estudiante/evaluaciones/${evaluacionId}/enviar/`)
      if (automatico) toast.info('El tiempo terminó: tu evaluación se envió automáticamente')
      else toast.success('Evaluación enviada')
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo enviar; se reintentará al recargar'))
    } finally {
      setEnviando(false)
      setConfirmar(null)
      setVersion((n) => n + 1)
    }
  }

  // Temporizador: cada segundo; al llegar a 0 envía una sola vez (HU-07.3).
  useEffect(() => {
    if (!enCurso) return
    const id = window.setInterval(() => {
      const t = Date.now()
      setAhora(t)
      if (venceEn - (t + desfase) <= 0 && !autoEnviado.current) {
        autoEnviado.current = true
        void enviar(true)
      }
    }, 1000)
    return () => window.clearInterval(id)
    // enviar solo usa setters y el id de la ruta; no necesita reiniciar el intervalo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enCurso, venceEn, desfase])

  const iniciar = async () => {
    // Pantalla completa dentro del clic (gesto del usuario). Si se rechaza, se sigue sin ella.
    marcarCambioPantalla()
    pantallaRechazada.current = !(await pedirPantallaCompleta())
    setIniciando(true)
    try {
      await api.post(`/evaluacion/estudiante/evaluaciones/${evaluacionId}/iniciar/`)
      autoEnviado.current = false
      setVersion((n) => n + 1)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo iniciar la evaluación'))
    } finally {
      setIniciando(false)
      setConfirmar(null)
    }
  }

  // HU-07.2: guarda al marcar; el indicador muestra si quedó registrada.
  const responder = async (preguntaId: number, opcion: number) => {
    const clave = String(preguntaId)
    setRespuestas((r) => ({ ...r, [clave]: opcion }))
    setGuardado((g) => ({ ...g, [clave]: 'guardando' }))
    try {
      await api.put(`/evaluacion/estudiante/evaluaciones/${evaluacionId}/respuestas/`, { pregunta: preguntaId, opcion })
      setGuardado((g) => ({ ...g, [clave]: 'guardada' }))
    } catch (err: unknown) {
      const estado = (err as { response?: { status?: number } }).response?.status
      setGuardado((g) => ({ ...g, [clave]: 'error' }))
      if (estado === 409) {
        toast.info(mensajeError(err, 'La evaluación ya fue enviada'))
        setVersion((n) => n + 1)
      } else {
        toast.error('No se guardó tu respuesta. Revisa tu conexión y vuelve a marcarla.')
      }
    }
  }

  // Con el intento en curso, salir pide confirmación (diálogo propio: un confirm()
  // nativo haría perder el foco y contaría como incidente).
  const volver = enCurso ? (
    <button type="button" onClick={() => setConfirmar('salir')} className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Volver a mis evaluaciones
    </button>
  ) : (
    <Link to="/mis-evaluaciones" className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Volver a mis evaluaciones
    </Link>
  )

  if (cargando) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }
  if (error || !detalle) {
    return (
      <div className="space-y-4">
        {volver}
        <p role="alert" className="text-sm text-destructive">{error || 'No se encontró la evaluación.'}</p>
      </div>
    )
  }

  const preguntas = detalle.preguntas ?? []
  const respondidas = Object.keys(respuestas).length
  const sinResponder = preguntas.length - respondidas
  const poco = restante <= 5 * 60 * 1000

  return (
    <div className="space-y-6">
      {volver}
      <div className="space-y-1">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-primary uppercase">{detalle.momento}</p>
        <h1 className="font-heading text-3xl text-foreground">{detalle.nombre}</h1>
      </div>

      {detalle.tipo === 'tarea' && (
        <Card>
          <CardContent className="p-6 text-sm">
            Esta evaluación se presenta entregando la tarea{' '}
            {detalle.tarea && (
              <Link to={`/mis-tareas/${detalle.tarea.id}`} className="font-medium text-primary hover:underline">
                {detalle.tarea.titulo}
              </Link>
            )}
            .
          </CardContent>
        </Card>
      )}

      {/* Antes de empezar */}
      {detalle.tipo === 'cuestionario' && !detalle.intento && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Antes de empezar</CardTitle>
            <CardDescription>
              {detalle.total_preguntas} preguntas · {detalle.duracion_minutos} minutos · disponible hasta{' '}
              {formatoFecha.format(new Date(detalle.fecha_fin))}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {detalle.instrucciones && <p className="text-sm whitespace-pre-line">{detalle.instrucciones}</p>}
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              <li>Tienes un solo intento.</li>
              <li>Cada respuesta se guarda al marcarla; puedes cambiarla mientras haya tiempo.</li>
              <li>El tiempo sigue corriendo aunque cierres la página. Al terminar, se envía automáticamente con lo que hayas respondido.</li>
            </ul>
            {!detalle.activa && <p role="alert" className="text-sm text-destructive">La evaluación no está disponible en este momento.</p>}
            {bloqueo ? (
              <div
                role="status"
                aria-live="polite"
                className={cn(
                  'flex items-start gap-3 rounded-lg p-3 text-sm',
                  esperandoLlamado ? 'bg-primary/10 text-foreground' : 'bg-destructive/10 text-foreground',
                )}
              >
                {esperandoLlamado ? (
                  <Hourglass className="mt-0.5 h-4 w-4 shrink-0 animate-pulse text-primary" aria-hidden />
                ) : (
                  <UserX className="mt-0.5 h-4 w-4 shrink-0 text-destructive" aria-hidden />
                )}
                <span>
                  <span className="block font-medium">{bloqueo}</span>
                  <span className="block text-muted-foreground">
                    {esperandoLlamado
                      ? 'Esta evaluación se presenta en sala. Podrás comenzar cuando el docente supervisor registre tu asistencia; esta página se actualiza sola.'
                      : 'El docente supervisor no te habilitó para presentar. Si es un error, habla con él en la sala.'}
                  </span>
                </span>
              </div>
            ) : (
              <Button onClick={() => setConfirmar('iniciar')} disabled={!detalle.activa || iniciando}>
                <Clock className="mr-1.5 h-4 w-4" aria-hidden />
                Comenzar evaluación
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Suspendido por integridad (ADR-010): tiempo congelado */}
      {suspendido && (
        <Card className="border-destructive/40">
          <CardContent className="space-y-2 p-6">
            <p role="alert" className="flex items-center gap-2 font-medium text-foreground">
              <PauseCircle className="h-5 w-5 text-destructive" aria-hidden />
              Evaluación suspendida: espera la decisión del docente.
            </p>
            <p className="text-sm text-muted-foreground">
              {integridad === 'suspendido' && 'Se registró un nuevo intento de copiar o salir de la evaluación. '}Tu tiempo está congelado
              {detalle.intento?.segundos_restantes != null && ` con ${reloj(detalle.intento.segundos_restantes * 1000)} restantes`}. Si el docente
              reactiva tu evaluación, continuarás con ese tiempo; esta página se actualiza sola.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Advertencia vigente (advertido o reactivado) */}
      {enCurso && (integridad === 'advertido' || integridad === 'reactivado') && (
        <p role="status" className="flex items-start gap-2 rounded-lg bg-warning/15 p-3 text-sm text-foreground">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
          {integridad === 'advertido'
            ? 'Ya tienes una advertencia: si vuelves a copiar o salir de la evaluación, se suspenderá.'
            : 'Tu evaluación fue reactivada. Un nuevo incidente la suspenderá de inmediato.'}
        </p>
      )}
      {enCurso && !enPantallaCompleta && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3 text-sm">
          <span className="text-muted-foreground">Presenta la evaluación en pantalla completa.</span>
          <Button variant="outline" size="sm" onClick={() => void volverAPantallaCompleta()}>
            <Maximize className="mr-1.5 h-4 w-4" aria-hidden />
            Pantalla completa
          </Button>
        </div>
      )}

      {/* En curso */}
      {enCurso && (
        <>
          {/* Barra fija abajo: siempre visible sin depender de qué contenedor hace scroll. */}
          <div className="fixed bottom-3 left-1/2 z-30 flex w-[calc(100%-1.5rem)] max-w-3xl -translate-x-1/2 items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-lg">
            <p
              className={cn('flex items-center gap-2 font-mono text-2xl font-bold', poco ? 'text-destructive' : 'text-foreground')}
              aria-label={`Tiempo restante ${reloj(restante)}`}
            >
              <Clock className="h-5 w-5" aria-hidden />
              {reloj(restante)}
            </p>
            <div className="hidden min-w-0 flex-1 sm:block" aria-live="polite">
              <p className="text-sm text-muted-foreground">
                {respondidas} de {preguntas.length} respondidas{sinResponder > 0 && ` · faltan ${sinResponder}`}
              </p>
              <div className="mt-1 h-1.5 rounded-full bg-muted" aria-hidden>
                <div className="h-1.5 rounded-full bg-primary" style={{ width: `${preguntas.length ? (100 * respondidas) / preguntas.length : 0}%` }} />
              </div>
            </div>
            <Button onClick={() => setConfirmar('enviar')} disabled={enviando}>
              {enviando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Send className="mr-1.5 h-4 w-4" aria-hidden />}
              Enviar evaluación
            </Button>
          </div>

          {/* Índice de preguntas: verde = respondida, contorno = pendiente. */}
          <nav aria-label="Preguntas" className="rounded-xl border border-border bg-card p-3">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-sm">
              <span className="text-muted-foreground">
                {respondidas} de {preguntas.length} respondidas{sinResponder > 0 && ` · ${sinResponder} pendiente(s)`}
              </span>
              {sinResponder > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const siguiente = preguntas.find((p) => respuestas[String(p.id)] === undefined)
                    if (siguiente) irAPregunta(siguiente.id)
                  }}
                >
                  Ir a la siguiente pendiente
                </Button>
              )}
            </div>
            <ol className="flex flex-wrap gap-1.5">
              {preguntas.map((p, i) => {
                const lista = respuestas[String(p.id)] !== undefined
                return (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => irAPregunta(p.id)}
                      aria-label={`Pregunta ${i + 1}: ${lista ? 'respondida' : 'pendiente'}`}
                      className={cn(
                        'h-8 w-8 rounded-lg border text-sm font-medium tabular-nums transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                        lista ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-foreground hover:bg-muted',
                      )}
                    >
                      {i + 1}
                    </button>
                  </li>
                )
              })}
            </ol>
          </nav>
          {/* Espacio inferior para que la barra fija no tape la última pregunta. */}
          {/* select-none: el contenido no se puede seleccionar durante el intento (ADR-010). */}
          <ol className="space-y-4 pb-24 select-none">
            {preguntas.map((p, i) => {
              const clave = String(p.id)
              const estado = guardado[clave]
              return (
                <li key={p.id} id={`pregunta-${p.id}`} className="scroll-mt-4">
                  <Card>
                    <CardContent className="space-y-3 p-4 sm:p-5">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-semibold text-primary">Pregunta {i + 1}</span>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground" aria-live="polite">
                          {estado === 'guardando' && <><Loader2 className="h-3 w-3 animate-spin" aria-hidden />Guardando…</>}
                          {estado === 'guardada' && <><Check className="h-3 w-3 text-success" aria-hidden />Guardada</>}
                          {estado === 'error' && (
                            <button
                              type="button"
                              className="flex items-center gap-1 text-destructive"
                              onClick={() => respuestas[clave] !== undefined && void responder(p.id, respuestas[clave])}
                            >
                              <RotateCcw className="h-3 w-3" aria-hidden />
                              No se guardó · reintentar
                            </button>
                          )}
                        </span>
                      </div>
                      {p.contexto && <p className="rounded-lg bg-muted p-3 text-sm whitespace-pre-line">{p.contexto}</p>}
                      <fieldset className="space-y-2">
                        <legend className="mb-2 font-medium whitespace-pre-line text-foreground">{p.enunciado}</legend>
                        {p.opciones.map((opcion, k) => {
                          const marcada = respuestas[clave] === k
                          return (
                            <label
                              key={k}
                              className={cn(
                                'flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors',
                                marcada ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted',
                              )}
                            >
                              <input
                                type="radio"
                                name={`pregunta-${p.id}`}
                                className="mt-0.5 h-4 w-4 shrink-0 accent-primary"
                                checked={marcada}
                                onChange={() => void responder(p.id, k)}
                              />
                              <span>{opcion}</span>
                            </label>
                          )
                        })}
                      </fieldset>
                    </CardContent>
                  </Card>
                </li>
              )
            })}
          </ol>
        </>
      )}

      {/* Enviada */}
      {detalle.intento?.estado === 'enviado' && anulado && (
        <Card className="border-destructive/40">
          <CardContent className="space-y-2 p-6">
            <p role="status" className="flex items-center gap-2 font-medium text-foreground">
              <Ban className="h-5 w-5 text-destructive" aria-hidden />
              Tu evaluación fue anulada por fraude por decisión del docente.
            </p>
            <p className="text-sm text-muted-foreground">Si tienes dudas sobre esta decisión, habla con tu docente o coordinador.</p>
          </CardContent>
        </Card>
      )}

      {detalle.intento?.estado === 'enviado' && !anulado && (
        <Card>
          <CardContent className="space-y-2 p-6">
            <p role="status" className="flex items-center gap-2 font-medium text-foreground">
              <CheckCircle2 className="h-5 w-5 text-success" aria-hidden />
              {detalle.intento.envio_automatico
                ? 'El tiempo terminó y tu evaluación se envió automáticamente.'
                : 'Tu evaluación fue enviada.'}
            </p>
            <p className="text-sm text-muted-foreground">
              {detalle.intento.enviado_en && `Enviada el ${formatoFecha.format(new Date(detalle.intento.enviado_en))} · `}
              {detalle.intento.respondidas} de {detalle.total_preguntas} preguntas respondidas.
            </p>
          </CardContent>
        </Card>
      )}

      <Dialog open={!!aviso} onOpenChange={(v) => !v && setAviso(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-warning" aria-hidden />
              Advertencia
            </DialogTitle>
            <DialogDescription>{aviso}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setAviso(null)}>Entendido, continuar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmar === 'iniciar'} onOpenChange={(v) => !v && setConfirmar(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>¿Comenzar la evaluación?</DialogTitle>
            <DialogDescription>
              Tendrás {detalle.duracion_minutos} minutos desde ahora y un solo intento.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmar(null)} disabled={iniciando}>
              Cancelar
            </Button>
            <Button onClick={() => void iniciar()} disabled={iniciando}>
              {iniciando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Comenzar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmar === 'salir'} onOpenChange={(v) => !v && setConfirmar(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>¿Salir de la evaluación?</DialogTitle>
            <DialogDescription>
              Tus respuestas ya están guardadas, pero el tiempo sigue corriendo aunque salgas. Al terminar se envía con lo que hayas respondido.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmar(null)}>
              Seguir respondiendo
            </Button>
            <Button variant="destructive" onClick={() => navegar('/mis-evaluaciones')}>
              Salir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmar === 'enviar'} onOpenChange={(v) => !v && setConfirmar(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>¿Enviar la evaluación?</DialogTitle>
            <DialogDescription>Después de enviarla no podrás cambiar tus respuestas.</DialogDescription>
          </DialogHeader>
          {sinResponder > 0 && (
            <p className="flex items-start gap-2 text-sm text-foreground">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
              Te faltan {sinResponder} pregunta(s) por responder.
            </p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmar(null)} disabled={enviando}>
              Seguir respondiendo
            </Button>
            <Button onClick={() => void enviar(false)} disabled={enviando}>
              {enviando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Enviar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
