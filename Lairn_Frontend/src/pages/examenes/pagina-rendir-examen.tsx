// Página para rendir un examen adaptativo.
// Inicia la sesión de examen con POST /motor-adaptativo/iniciar/,
// muestra preguntas generadas por la IA y permite al estudiante responder.
// El feedback de cada respuesta y el resultado final se muestran como modales.

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Loader2,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Trophy,
  BookOpen,
  Send,
  RotateCw,
  SignalLow,
  SignalMedium,
  SignalHigh,
  Clock,
} from 'lucide-react'
import { toast } from 'sonner'
import type { SesionExamen, ResultadoExamen } from '@/types/examen'

// Configuración visual de dificultad.
const dificultadConfig: Record<number, { label: string; clase: string; icono: typeof SignalLow }> = {
  1: { label: 'Fácil', clase: 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800', icono: SignalLow },
  2: { label: 'Media', clase: 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800', icono: SignalMedium },
  3: { label: 'Difícil', clase: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800', icono: SignalHigh },
}

// Estados visuales de la página (sin feedback ni resultado — esos van en modales).
type EstadoPagina = 'iniciando' | 'pregunta' | 'error'

export default function PaginaRendirExamen() {
  const { cursoId, examenId } = useParams<{ cursoId: string; examenId: string }>()

  // Estado de la sesión y pregunta actual.
  const [sesion, setSesion] = useState<SesionExamen | null>(null)
  const [seleccionada, setSeleccionada] = useState<string | null>(null)
  const [estadoPagina, setEstadoPagina] = useState<EstadoPagina>('iniciando')
  const [respondiendo, setRespondiendo] = useState(false)
  const [resultado, setResultado] = useState<ResultadoExamen | null>(null)

  // Estado de los modales.
  const [feedbackAbierto, setFeedbackAbierto] = useState(false)
  const [feedbackCorrecta, setFeedbackCorrecta] = useState(false)
  const [feedbackRetroalimentacion, setFeedbackRetroalimentacion] = useState<SesionExamen['retroalimentacion']>(null)
  const [resultadoAbierto, setResultadoAbierto] = useState(false)

  // Contador regresivo del examen (en segundos).
  const [tiempoRestante, setTiempoRestante] = useState(0)

  // Datos pendientes de procesar después de cerrar el modal de feedback.
  const datosSiguientesRef = useRef<SesionExamen | null>(null)
  const examenTerminadoRef = useRef(false)
  const correctasAnterioresRef = useRef(0)

  // Timestamp de cuándo se mostró la pregunta actual (para calcular tiempo_segundos).
  const preguntaMostradaEn = useRef(0)

  // sesion_id se guarda en ref para no perderlo si el backend no lo devuelve en /responder/.
  const sesionIdRef = useRef<number | null>(null)

  // Inicia la sesión de examen al montar.
  useEffect(() => {
    // AbortController para cancelar la request si el componente se desmonta
    // (StrictMode en dev desmonta y re-monta inmediatamente).
    const controller = new AbortController()

    const iniciarExamen = async () => {
      if (!examenId) {
        setEstadoPagina('error')
        return
      }

      const idNumerico = Number(examenId)
      if (isNaN(idNumerico)) {
        setEstadoPagina('error')
        return
      }

      try {
        const { data } = await api.post<SesionExamen>('/motor-adaptativo/iniciar/', {
          examen_id: idNumerico,
        }, {
          signal: controller.signal,
        })
        setSesion(data)
        sesionIdRef.current = data.sesion_id
        setTiempoRestante(data.tiempo_total_minutos * 60)
        preguntaMostradaEn.current = Date.now()
        setEstadoPagina('pregunta')
      } catch (err: unknown) {
        // Ignorar si fue abortado por cleanup de StrictMode.
        if (controller.signal.aborted) return

        const axiosErr = err as { response?: { data?: Record<string, string[]> } }

        const data = axiosErr.response?.data
        if (data) {
          const mensajes = Object.values(data).flat().join('. ')
          toast.error(mensajes)
        } else {
          toast.error('No se pudo iniciar el examen')
        }
        setEstadoPagina('error')
      }
    }
    iniciarExamen()

    return () => { controller.abort() }
  }, [examenId])

  // Procesa la respuesta del estudiante.
  const enviarRespuesta = useCallback(async () => {
    if (!seleccionada || !sesionIdRef.current) return
    setRespondiendo(true)
    try {
      const { data } = await api.post<SesionExamen>(
        `/motor-adaptativo/${sesionIdRef.current}/responder/`,
        {
          respuesta: seleccionada,
          tiempo_segundos: Math.round((Date.now() - preguntaMostradaEn.current) / 1000),
        }
      )

      // Determinar si la respuesta fue correcta.
      // Cuando completado=true, el backend no devuelve es_correcta en la raíz.
      // Se infiere comparando el total de correctas con el anterior.
      let esCorrecta: boolean
      if (data.es_correcta !== undefined) {
        esCorrecta = data.es_correcta
      } else if (data.retroalimentacion?.es_correcta !== undefined) {
        esCorrecta = data.retroalimentacion.es_correcta
      } else if (data.completado && data.correctas !== undefined) {
        esCorrecta = data.correctas > correctasAnterioresRef.current
      } else {
        esCorrecta = false
      }
      setFeedbackCorrecta(esCorrecta)
      setFeedbackRetroalimentacion(data.retroalimentacion ?? null)

      // Actualizar contador de correctas para la próxima respuesta.
      if (data.correctas !== undefined) {
        correctasAnterioresRef.current = data.correctas
      }

      const examenTerminado = data.completado || data.pregunta_numero > data.total_preguntas
      examenTerminadoRef.current = examenTerminado
      datosSiguientesRef.current = data

      // Abrir modal de feedback (el botón Aceptar cierra y avanza).
      setFeedbackAbierto(true)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      if (data) {
        const mensajes = Object.values(data).flat().join('. ')
        toast.error(mensajes)
      } else {
        toast.error('No se pudo enviar la respuesta')
      }
    } finally {
      setRespondiendo(false)
    }
  }, [seleccionada])

  // Cierra el modal de feedback y avanza a la siguiente pregunta o muestra resultados.
  const cerrarFeedback = useCallback(() => {
    const data = datosSiguientesRef.current
    setFeedbackAbierto(false)

    if (examenTerminadoRef.current && data) {
      setResultado({
        puntaje: data.puntaje ?? 0,
        nota: data.nota ?? 0,
        correctas: data.correctas ?? 0,
        total_preguntas: data.total_preguntas,
      })
      setResultadoAbierto(true)
    } else if (data) {
      setSesion(data)
      preguntaMostradaEn.current = Date.now()
      setSeleccionada(null)
    }

    datosSiguientesRef.current = null
    setFeedbackRetroalimentacion(null)
  }, [])

  // Contador regresivo del examen.
  useEffect(() => {
    if (estadoPagina !== 'pregunta') return

    const intervalo = setInterval(() => {
      setTiempoRestante((prev) => {
        if (prev <= 1) {
          clearInterval(intervalo)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => { clearInterval(intervalo) }
  }, [estadoPagina])

  // Formatea segundos a MM:SS.
  const formatearTiempo = (segundos: number) => {
    const m = Math.floor(segundos / 60)
    const s = segundos % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  // --- Renderizado ---

  // Estado de carga: spinner mientras inicia el examen.
  if (estadoPagina === 'iniciando') {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Iniciando examen...</p>
      </div>
    )
  }

  // Estado de error: no se pudo iniciar.
  if (estadoPagina === 'error') {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <XCircle className="h-12 w-12 text-destructive" />
        <p className="text-sm text-muted-foreground">No se pudo iniciar el examen</p>
        <Link
          to={`/mis-cursos/${cursoId}/examenes`}
          className="inline-flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a exámenes
        </Link>
      </div>
    )
  }

  // Estado de pregunta activa (siempre visible cuando estadoPagina === 'pregunta').
  if (sesion) {
    const dif = dificultadConfig[sesion.dificultad_actual] || dificultadConfig[1]
    const IconoDificultad = dif.icono
    const preguntaDeshabilitada = respondiendo || feedbackAbierto || resultadoAbierto

    return (
      <>
        <div className={`mx-auto max-w-2xl space-y-6 transition-opacity ${preguntaDeshabilitada ? 'opacity-50 pointer-events-none' : ''}`}>
          {/* Encabezado */}
          <div className="flex items-center justify-between">
            <Link
              to={`/mis-cursos/${cursoId}/examenes`}
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Abandonar examen
            </Link>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${tiempoRestante <= 60 ? 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800' : ''}`}>
                <Clock className="h-3 w-3" />
                {formatearTiempo(tiempoRestante)}
              </span>
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${dif.clase}`}>
                <IconoDificultad className="h-3 w-3" />
                {dif.label}
              </span>
            </div>
          </div>

          {/* Progreso */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>Pregunta {sesion.pregunta_numero} de {sesion.total_preguntas}</span>
              <div className="flex items-center gap-1.5">
                <RotateCw className="h-3.5 w-3.5" />
                <span>{sesion.intento_actual} / {sesion.max_intentos} intentos</span>
              </div>
            </div>
          </div>

          {/* Card de la pregunta */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Modo: {sesion.modo}
                </span>
              </div>
              <CardTitle className="text-lg leading-relaxed">
                {sesion.pregunta}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Explicación (solo en modo guiado) */}
              {sesion.explicacion && (
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950/20">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    <span className="font-medium">Pista: </span>
                    {sesion.explicacion}
                  </p>
                </div>
              )}

              {/* Opciones de respuesta */}
              <div className="space-y-3">
                {sesion.opciones.map((opcion, i) => (
                  <button
                    key={i}
                    type="button"
                    disabled={preguntaDeshabilitada}
                    className={`flex w-full items-center space-x-3 rounded-lg border p-4 text-left transition-colors cursor-pointer hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-60 ${
                      seleccionada === opcion
                        ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                        : 'border-border'
                    }`}
                    onClick={() => setSeleccionada(opcion)}
                  >
                    <span
                      className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                        seleccionada === opcion
                          ? 'border-primary bg-primary'
                          : 'border-input'
                      }`}
                    >
                      {seleccionada === opcion && (
                        <span className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />
                      )}
                    </span>
                    <span className="flex-1 text-sm">{opcion}</span>
                  </button>
                ))}
              </div>

              {/* Botón enviar */}
              <Button
                className="w-full"
                size="lg"
                disabled={!seleccionada || preguntaDeshabilitada}
                onClick={enviarRespuesta}
              >
                {respondiendo ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Responder
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Modal de Feedback */}
        <Dialog open={feedbackAbierto} onOpenChange={() => {}}>
          <DialogContent className="sm:max-w-xs [&>button]:hidden">
            <DialogHeader className="sr-only">
              <DialogTitle>Resultado de la respuesta</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col items-center gap-4 py-4">
              {feedbackCorrecta ? (
                <>
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/20">
                    <CheckCircle2 className="h-10 w-10 text-emerald-500" />
                  </div>
                  <p className="text-2xl font-bold text-emerald-500">¡Correcto!</p>
                </>
              ) : (
                <>
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-50 dark:bg-red-950/20">
                    <XCircle className="h-10 w-10 text-destructive" />
                  </div>
                  <p className="text-2xl font-bold text-destructive">Incorrecto</p>
                  {feedbackRetroalimentacion && (
                    <p className="text-sm text-muted-foreground text-center">
                      Respuesta correcta: <span className="font-medium text-foreground">{feedbackRetroalimentacion.respuesta_correcta}</span>
                    </p>
                  )}
                </>
              )}
              {feedbackRetroalimentacion?.concepto && (
                <p className="text-xs text-muted-foreground">
                  Concepto: <span className="font-medium">{feedbackRetroalimentacion.concepto}</span>
                </p>
              )}
              <Button onClick={cerrarFeedback} className="w-full mt-2">
                Aceptar
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Modal de Resultado Final */}
        <Dialog open={resultadoAbierto} onOpenChange={() => {}}>
          <DialogContent className="sm:max-w-md [&>button]:hidden">
            <DialogHeader className="sr-only">
              <DialogTitle>Examen Completado</DialogTitle>
            </DialogHeader>
            {resultado && (
              <div className="space-y-6 py-2">
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                    <Trophy className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold">Examen Completado</h2>
                </div>

                {/* Nota grande */}
                <div className="text-center">
                  <p className="text-5xl font-bold text-primary">
                    {resultado.nota.toFixed(1)}
                  </p>
                  <p className="text-sm text-muted-foreground">de 5.0</p>
                </div>

                {/* Barra de progreso */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Puntaje</span>
                    <span>{resultado.puntaje.toFixed(1)}%</span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{ width: `${resultado.puntaje}%` }}
                    />
                  </div>
                </div>

                {/* Estadísticas */}
                <div className="flex justify-center gap-8 text-center">
                  <div>
                    <p className="text-2xl font-bold text-emerald-600">
                      {resultado.correctas}
                    </p>
                    <p className="text-xs text-muted-foreground">Correctas</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-muted-foreground">
                      {resultado.total_preguntas}
                    </p>
                    <p className="text-xs text-muted-foreground">Total</p>
                  </div>
                </div>

                {/* Botón volver */}
                <Link
                  to={`/mis-cursos/${cursoId}/examenes`}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Volver a exámenes
                </Link>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </>
    )
  }

  // Fallback.
  return (
    <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
      <XCircle className="h-12 w-12 text-destructive" />
      <p className="text-sm text-muted-foreground">Estado inesperado</p>
      <Link
        to={`/mis-cursos/${cursoId}/examenes`}
        className="inline-flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver a exámenes
      </Link>
    </div>
  )
}
