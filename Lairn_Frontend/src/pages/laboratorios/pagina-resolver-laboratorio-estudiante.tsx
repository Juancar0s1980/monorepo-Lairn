// Resolución de un laboratorio, para el rol Estudiante.
//
// Tres modos según `pregunta.tipo`:
// - "codigo": layout tipo "juez en línea" (LeetCode) — enunciado + ejemplos
//   a la izquierda, editor de código + resultado de ejecución a la derecha.
//   "Ejecutar" corre el código contra los casos de test PÚBLICOS en el
//   sandbox del microservicio ejecutor — no guarda nada (ver
//   vista_ejecutar_codigo.py). "Enviar" corre contra todos los casos y
//   guarda un intento.
// - "respuesta_libre": sin "Ejecutar" (no aplica a un ensayo) ni casos de
//   test — un textarea libre y "Enviar" califica con IA contra la rúbrica
//   del docente, devolviendo puntaje + retroalimentación (ver
//   agente_evaluador.evaluar_respuesta_libre en backend).
// - "problema_visual": opción múltiple con diagrama. Cada estudiante tiene
//   asignada una VARIANTE propia (`pregunta.mi_variante`: su propio diagrama
//   + sus propias 4 opciones, sorteada la primera vez que la pide y fija
//   desde entonces). El estudiante resuelve a mano en papel y solo
//   selecciona la opción correcta — "Enviar" manda JSON normal
//   ({opcion_seleccionada}) y la calificación es instantánea (comparación
//   exacta, sin IA de por medio).
// - "pronunciacion": el estudiante escucha `pregunta.audio_referencia`
//   (generado con Edge TTS) y graba su propia voz con el micrófono
//   (MediaRecorder). "Enviar" manda la grabación como multipart — el backend
//   la transcribe con Whisper y compara el texto contra
//   `pregunta.texto_pronunciar` para el puntaje (ver agente_pronunciacion.py).

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '@/services/api'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { EditorCodigo } from '@/components/editor-codigo'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft, Check, CheckCircle2, Clock, Code2, FlaskConical, Loader2, Mic, NotebookPen, Play, Send, Square, Trophy, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import type {
  LaboratorioDetalleEstudiante,
  MisEntregas,
  ResultadoEjecucion,
  ResultadoEnvio,
  ResultadoFinalizarPractica,
} from '@/types/laboratorio'

// Formatea un ISO a fecha/hora legible en español.
function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
}

export default function PaginaResolverLaboratorioEstudiante() {
  const { cursoId, laboratorioId } = useParams<{ cursoId: string; laboratorioId: string }>()

  const [laboratorio, setLaboratorio] = useState<LaboratorioDetalleEstudiante | null>(null)
  const [cargando, setCargando] = useState(true)
  const [indiceActivo, setIndiceActivo] = useState(0)

  // Respuesta por pregunta (id -> texto actual: código o ensayo), para no perder progreso al cambiar de pregunta.
  const [respuestas, setRespuestas] = useState<Record<number, string>>({})
  const [ejecutando, setEjecutando] = useState(false)
  const [resultado, setResultado] = useState<ResultadoEjecucion | null>(null)

  const [enviando, setEnviando] = useState(false)
  const [resultadoEnvio, setResultadoEnvio] = useState<ResultadoEnvio | null>(null)
  const [misEntregas, setMisEntregas] = useState<MisEntregas | null>(null)

  // Opción elegida (0-3), solo para preguntas tipo='problema_visual'.
  const [opcionSeleccionada, setOpcionSeleccionada] = useState<number | null>(null)

  // Grabación del micrófono, solo para preguntas tipo='pronunciacion'.
  const [grabando, setGrabando] = useState(false)
  const [audioGrabado, setAudioGrabado] = useState<Blob | null>(null)
  const [audioGrabadoUrl, setAudioGrabadoUrl] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const fragmentosAudioRef = useRef<Blob[]>([])

  // Ids de preguntas con al menos una entrega (para saber si ya se puede "Finalizar
  // práctica" cuando el laboratorio es la práctica de un examen). Se siembra al cargar
  // consultando el historial de cada pregunta, y se actualiza localmente al enviar.
  const [preguntasConEntrega, setPreguntasConEntrega] = useState<Set<number>>(new Set())
  const [finalizando, setFinalizando] = useState(false)
  const [resultadoFinal, setResultadoFinal] = useState<ResultadoFinalizarPractica | null>(null)

  useEffect(() => {
    if (!cursoId || !laboratorioId) return
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<LaboratorioDetalleEstudiante>(
          `/laboratorios/mis-cursos/${cursoId}/laboratorios/${laboratorioId}/`,
          { signal: controlador.signal }
        )
        setLaboratorio(data)
        const inicial: Record<number, string> = {}
        for (const p of data.preguntas) inicial[p.id] = p.codigo_inicial
        setRespuestas(inicial)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudo cargar el laboratorio')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId, laboratorioId])

  // Si el laboratorio es la práctica de un examen, siembra qué preguntas ya
  // tienen entregas previas (de esta sesión o de una anterior) para habilitar
  // "Finalizar práctica" solo cuando todas están respondidas.
  useEffect(() => {
    if (!laboratorio || !laboratorio.examen) return
    const controlador = new AbortController()
    Promise.all(
      laboratorio.preguntas.map((p) =>
        api
          .get<MisEntregas>(`/laboratorios/preguntas/${p.id}/mis-entregas/`, { signal: controlador.signal })
          .then(({ data }) => (data.entregas.length > 0 ? p.id : null))
          .catch(() => null)
      )
    ).then((ids) => {
      if (controlador.signal.aborted) return
      setPreguntasConEntrega(new Set(ids.filter((id): id is number => id !== null)))
    })
    return () => controlador.abort()
  }, [laboratorio])

  const preguntaActivaId = laboratorio?.preguntas[indiceActivo]?.id

  // Carga el historial de intentos de la pregunta activa (para mostrar "X/Y intentos usados").
  useEffect(() => {
    if (!preguntaActivaId) return
    const controlador = new AbortController()
    api
      .get<MisEntregas>(`/laboratorios/preguntas/${preguntaActivaId}/mis-entregas/`, { signal: controlador.signal })
      .then(({ data }) => setMisEntregas(data))
      .catch(() => {
        if (!controlador.signal.aborted) setMisEntregas(null)
      })
    return () => controlador.abort()
  }, [preguntaActivaId])

  if (cargando) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!laboratorio || laboratorio.preguntas.length === 0) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-2 text-center">
        <Code2 className="h-10 w-10 text-muted-foreground/50" />
        <p className="text-sm font-medium text-muted-foreground">
          {laboratorio ? 'Este laboratorio todavía no tiene preguntas' : 'Laboratorio no encontrado'}
        </p>
      </div>
    )
  }

  const pregunta = laboratorio.preguntas[indiceActivo]
  const esCodigo = pregunta.tipo === 'codigo'
  const esVisual = pregunta.tipo === 'problema_visual'
  const esPronunciacion = pregunta.tipo === 'pronunciacion'

  const iniciarGrabacion = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      fragmentosAudioRef.current = []
      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) fragmentosAudioRef.current.push(e.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(fragmentosAudioRef.current, { type: recorder.mimeType || 'audio/webm' })
        setAudioGrabado(blob)
        setAudioGrabadoUrl(URL.createObjectURL(blob))
        stream.getTracks().forEach((t) => t.stop())
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setGrabando(true)
    } catch {
      toast.error('No se pudo acceder al micrófono. Revisa los permisos del navegador.')
    }
  }

  const detenerGrabacion = () => {
    mediaRecorderRef.current?.stop()
    setGrabando(false)
  }

  const ejecutar = async () => {
    setEjecutando(true)
    setResultado(null)
    setResultadoEnvio(null)
    try {
      const { data } = await api.post<ResultadoEjecucion>(
        `/laboratorios/preguntas/${pregunta.id}/ejecutar/`,
        { codigo: respuestas[pregunta.id] ?? '' }
      )
      setResultado(data)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudo ejecutar el código')
    } finally {
      setEjecutando(false)
    }
  }

  const enviar = async () => {
    if (esVisual && opcionSeleccionada === null) return
    if (esPronunciacion && !audioGrabado) return
    setEnviando(true)
    setResultado(null)
    setResultadoEnvio(null)
    try {
      let data: ResultadoEnvio
      if (esPronunciacion) {
        const formData = new FormData()
        formData.append('audio', audioGrabado!, 'grabacion.webm')
        const resp = await api.post<ResultadoEnvio>(
          `/laboratorios/preguntas/${pregunta.id}/enviar/`,
          formData,
          { headers: { 'Content-Type': undefined } }
        )
        data = resp.data
      } else {
        const resp = await api.post<ResultadoEnvio>(
          `/laboratorios/preguntas/${pregunta.id}/enviar/`,
          esVisual ? { opcion_seleccionada: opcionSeleccionada } : { respuesta: respuestas[pregunta.id] ?? '' }
        )
        data = resp.data
      }
      setResultadoEnvio(data)
      setPreguntasConEntrega((prev) => new Set(prev).add(pregunta.id))
      setMisEntregas((prev) =>
        prev
          ? {
              ...prev,
              intentos_usados: prev.intentos_usados + 1,
              intentos_restantes: data.intentos_restantes,
              entregas: [...prev.entregas, {
                id: data.id, intento: data.intento, casos_pasados: data.casos_pasados,
                casos_totales: data.casos_totales, puntaje: data.puntaje,
                retroalimentacion: data.retroalimentacion, opcion_seleccionada: data.opcion_seleccionada,
                transcripcion: data.transcripcion,
                enviado_en: data.enviado_en,
              }],
            }
          : prev
      )
      toast.success(
        esCodigo
          ? `Enviado: ${data.puntaje}% (${data.casos_pasados}/${data.casos_totales} casos)`
          : `Enviado: ${data.puntaje}%`
      )
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudo enviar la respuesta')
    } finally {
      setEnviando(false)
    }
  }

  const cambiarPregunta = (indice: number) => {
    setIndiceActivo(indice)
    setResultado(null)
    setResultadoEnvio(null)
    setOpcionSeleccionada(null)
    if (grabando) mediaRecorderRef.current?.stop()
    setGrabando(false)
    setAudioGrabado(null)
    if (audioGrabadoUrl) URL.revokeObjectURL(audioGrabadoUrl)
    setAudioGrabadoUrl(null)
  }

  const sinIntentos = misEntregas?.intentos_restantes === 0
  const fechaLimiteSuperada = !!(laboratorio && misEntregas?.fecha_limite && new Date(misEntregas.fecha_limite) < new Date())

  const esPracticaDeExamen = !!laboratorio?.examen
  const todasRespondidas = esPracticaDeExamen && laboratorio!.preguntas.every((p) => preguntasConEntrega.has(p.id))

  const finalizarPractica = async () => {
    if (!laboratorioId) return
    setFinalizando(true)
    try {
      const { data } = await api.post<ResultadoFinalizarPractica>(
        `/laboratorios/laboratorios/${laboratorioId}/finalizar-practica/`
      )
      setResultadoFinal(data)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudo finalizar la práctica')
    } finally {
      setFinalizando(false)
    }
  }

  return (
    <div className="space-y-4">
      <EncabezadoGradiente
        titulo={laboratorio.titulo}
        subtitulo={laboratorio.instrucciones || 'Resuelve las preguntas del laboratorio'}
        volverA={`/mis-cursos/${cursoId}/examenes`}
        volverTexto="Volver al curso"
      />

      {/* Banner de "finalizar práctica", solo si este laboratorio es la práctica de un examen */}
      {esPracticaDeExamen && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
          <div className="flex items-center gap-2 text-sm">
            <FlaskConical className="h-4 w-4 text-primary" />
            <span>Esta es la práctica de un examen. Responde todas las preguntas para ver tu nota final.</span>
          </div>
          <Button
            size="sm"
            onClick={finalizarPractica}
            disabled={!todasRespondidas || finalizando}
            title={!todasRespondidas ? 'Responde todas las preguntas antes de finalizar' : undefined}
          >
            {finalizando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trophy className="h-3.5 w-3.5" />}
            Finalizar práctica y ver nota final
          </Button>
        </div>
      )}

      {/* Selector de pregunta, si el laboratorio tiene más de una */}
      {laboratorio.preguntas.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {laboratorio.preguntas.map((p, i) => (
            <button
              key={p.id}
              type="button"
              onClick={() => cambiarPregunta(i)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                i === indiceActivo
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border text-muted-foreground hover:bg-muted'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2 lg:items-start">
        {/* Panel izquierdo: enunciado + ejemplos (solo código) */}
        <Card>
          <CardContent className="space-y-4 pt-5">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="uppercase">
                {esCodigo
                  ? pregunta.lenguaje
                  : esVisual
                    ? 'Problema con imagen'
                    : esPronunciacion
                      ? 'Pronunciación'
                      : 'Respuesta abierta'}
              </Badge>
              <Badge variant="secondary">{pregunta.puntos} pts</Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm">{pregunta.enunciado}</p>

            {esVisual && pregunta.mi_variante && (
              <img
                src={pregunta.mi_variante.imagen}
                alt="Diagrama del problema"
                className="w-full rounded-lg border object-contain"
              />
            )}

            {esPronunciacion && (
              <div className="space-y-2 rounded-lg border p-4 text-center">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Pronuncia</p>
                <p className="text-2xl font-bold">{pregunta.texto_pronunciar}</p>
                {pregunta.audio_referencia && (
                  <audio controls src={pregunta.audio_referencia} className="mx-auto mt-2 h-9 w-full max-w-xs" />
                )}
              </div>
            )}

            {esCodigo && pregunta.lenguaje === 'sql' && pregunta.setup_sql && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Esquema</p>
                <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-xs">{pregunta.setup_sql}</pre>
              </div>
            )}

            {esCodigo && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Ejemplos</p>
                {pregunta.casos_test.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Esta pregunta no tiene ejemplos públicos.</p>
                ) : (
                  pregunta.casos_test.map((caso, i) => (
                    <div key={caso.id} className="space-y-1 rounded-lg border p-3 text-xs">
                      <p className="font-semibold text-muted-foreground">Ejemplo {i + 1}</p>
                      {caso.entrada && (
                        <p>
                          <span className="text-muted-foreground">Entrada: </span>
                          <code className="rounded bg-muted px-1 py-0.5">{caso.entrada}</code>
                        </p>
                      )}
                      <p>
                        <span className="text-muted-foreground">Salida esperada: </span>
                        <code className="rounded bg-muted px-1 py-0.5">{caso.salida_esperada}</code>
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Panel derecho: editor/textarea + ejecutar (solo código) + resultado */}
        <Card>
          <CardContent className="space-y-3 pt-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tu respuesta</p>
              <div className="flex items-center gap-2">
                {misEntregas && (
                  <Badge variant="outline" className="text-xs">
                    {misEntregas.max_intentos
                      ? `${misEntregas.intentos_usados}/${misEntregas.max_intentos} intentos`
                      : `${misEntregas.intentos_usados} intento(s)`}
                  </Badge>
                )}
                {esCodigo && (
                  <Button size="sm" variant="outline" onClick={ejecutar} disabled={ejecutando}>
                    {ejecutando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                    Ejecutar
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={enviar}
                  disabled={
                    enviando || sinIntentos || fechaLimiteSuperada ||
                    (esVisual && opcionSeleccionada === null) ||
                    (esPronunciacion && !audioGrabado)
                  }
                  title={
                    sinIntentos
                      ? 'Ya usaste todos tus intentos para esta pregunta'
                      : fechaLimiteSuperada
                        ? 'La fecha límite ya pasó'
                        : esVisual && opcionSeleccionada === null
                          ? 'Selecciona una opción primero'
                          : esPronunciacion && !audioGrabado
                            ? 'Graba tu voz primero'
                            : undefined
                  }
                >
                  {enviando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  Enviar
                </Button>
              </div>
            </div>

            {misEntregas?.fecha_limite && (
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                Fecha límite: {formatearFecha(misEntregas.fecha_limite)}
                {fechaLimiteSuperada && <span className="text-destructive"> (superada)</span>}
              </p>
            )}

            {esCodigo ? (
              <EditorCodigo
                lenguaje={pregunta.lenguaje}
                valor={respuestas[pregunta.id] ?? ''}
                onChange={(valor) => setRespuestas((prev) => ({ ...prev, [pregunta.id]: valor }))}
                altura="280px"
              />
            ) : esVisual ? (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  Resuelve el problema a mano en papel usando el diagrama, y selecciona la respuesta correcta.
                </p>
                {(pregunta.mi_variante?.opciones ?? []).map((opcion, i) => (
                  <button
                    key={i}
                    type="button"
                    disabled={enviando || !!resultadoEnvio}
                    onClick={() => setOpcionSeleccionada(i)}
                    className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-70 ${
                      opcionSeleccionada === i
                        ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                        : 'border-border hover:bg-muted/50'
                    }`}
                  >
                    <span
                      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                        opcionSeleccionada === i ? 'border-primary bg-primary text-primary-foreground' : 'border-input'
                      }`}
                    >
                      {String.fromCharCode(65 + i)}
                    </span>
                    <span className="flex-1">{opcion}</span>
                    {opcionSeleccionada === i && <Check className="h-4 w-4 text-primary" />}
                  </button>
                ))}
              </div>
            ) : esPronunciacion ? (
              <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-6">
                <p className="text-xs text-muted-foreground">
                  Escucha la pronunciación correcta a la izquierda, luego graba tu propia voz diciendo la
                  misma palabra o frase.
                </p>
                {!grabando ? (
                  <Button
                    type="button"
                    variant="outline"
                    disabled={enviando || !!resultadoEnvio}
                    onClick={iniciarGrabacion}
                  >
                    <Mic className="h-4 w-4" />
                    {audioGrabado ? 'Grabar de nuevo' : 'Grabar'}
                  </Button>
                ) : (
                  <Button type="button" variant="destructive" onClick={detenerGrabacion}>
                    <Square className="h-4 w-4" />
                    Detener
                  </Button>
                )}
                {grabando && (
                  <p className="flex items-center gap-1.5 text-xs text-destructive">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-destructive" />
                    Grabando...
                  </p>
                )}
                {audioGrabadoUrl && !grabando && (
                  <div className="w-full max-w-xs space-y-1 text-center">
                    <p className="text-xs text-muted-foreground">Tu grabación:</p>
                    <audio controls src={audioGrabadoUrl} className="w-full" />
                  </div>
                )}
              </div>
            ) : (
              <Textarea
                rows={12}
                placeholder="Escribe tu respuesta aquí..."
                value={respuestas[pregunta.id] ?? ''}
                onChange={(e) => setRespuestas((prev) => ({ ...prev, [pregunta.id]: e.target.value }))}
              />
            )}

            {/* Resultado de la ejecución (solo código) */}
            {esCodigo && resultado && (
              <div className="space-y-2 border-t pt-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Resultado
                  </p>
                  <Badge variant={resultado.casos_publicos_pasados === resultado.casos_publicos_totales ? 'default' : 'destructive'}>
                    {resultado.casos_publicos_pasados}/{resultado.casos_publicos_totales} casos pasados
                  </Badge>
                </div>
                {resultado.resultados.map((r, i) => (
                  <div key={r.caso_test_id} className="space-y-1 rounded-lg border p-3 text-xs">
                    <div className="flex items-center gap-1.5 font-medium">
                      {r.paso ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-destructive" />
                      )}
                      Caso {i + 1} {r.timeout && '· tiempo excedido'}
                    </div>
                    {!r.paso && (
                      <div className="space-y-0.5 text-muted-foreground">
                        <p>Esperado: <code className="rounded bg-muted px-1 py-0.5">{r.salida_esperada}</code></p>
                        <p>Obtenido: <code className="rounded bg-muted px-1 py-0.5">{r.salida_obtenida || '(vacío)'}</code></p>
                        {r.stderr && <p className="text-destructive">{r.stderr}</p>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Resultado del envío calificado */}
            {resultadoEnvio && (
              <div className="space-y-2 border-t pt-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Resultado del envío (intento {resultadoEnvio.intento})
                  </p>
                  <Badge variant={resultadoEnvio.puntaje === 100 ? 'default' : 'destructive'}>
                    {resultadoEnvio.puntaje}%
                    {esCodigo && ` · ${resultadoEnvio.casos_pasados}/${resultadoEnvio.casos_totales} casos`}
                  </Badge>
                </div>

                {esVisual && resultadoEnvio.respuesta_correcta !== null && resultadoEnvio.respuesta_correcta !== undefined && (
                  <div className="flex items-center gap-2 rounded-lg border p-3 text-xs">
                    {resultadoEnvio.puntaje === 100 ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                    ) : (
                      <XCircle className="h-4 w-4 shrink-0 text-destructive" />
                    )}
                    <span className="text-muted-foreground">
                      {resultadoEnvio.puntaje === 100
                        ? '¡Correcto!'
                        : `Incorrecto. La respuesta correcta era la opción ${String.fromCharCode(65 + resultadoEnvio.respuesta_correcta)}.`}
                    </span>
                  </div>
                )}

                {esPronunciacion && resultadoEnvio.transcripcion !== null && resultadoEnvio.transcripcion !== undefined && (
                  <div className="flex items-center gap-2 rounded-lg border p-3 text-xs">
                    {resultadoEnvio.puntaje >= 80 ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                    ) : (
                      <XCircle className="h-4 w-4 shrink-0 text-destructive" />
                    )}
                    <div className="text-muted-foreground">
                      <p>Se esperaba: <span className="font-medium text-foreground">{pregunta.texto_pronunciar}</span></p>
                      <p>Se entendió: <span className="font-medium text-foreground">{resultadoEnvio.transcripcion || '(nada)'}</span></p>
                    </div>
                  </div>
                )}

                {!esCodigo && resultadoEnvio.retroalimentacion && (
                  <div className="flex items-start gap-2 rounded-lg border p-3 text-xs">
                    <NotebookPen className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    <p className="text-muted-foreground">{resultadoEnvio.retroalimentacion}</p>
                  </div>
                )}

                {esCodigo && resultadoEnvio.resultados.map((r, i) => (
                  <div key={r.caso_test_id} className="space-y-1 rounded-lg border p-3 text-xs">
                    <div className="flex items-center gap-1.5 font-medium">
                      {r.paso ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-destructive" />
                      )}
                      Caso {i + 1} {!r.es_publico && '(oculto)'} {r.timeout && '· tiempo excedido'}
                    </div>
                    {!r.paso && r.es_publico && (
                      <div className="space-y-0.5 text-muted-foreground">
                        <p>Esperado: <code className="rounded bg-muted px-1 py-0.5">{r.salida_esperada}</code></p>
                        <p>Obtenido: <code className="rounded bg-muted px-1 py-0.5">{r.salida_obtenida || '(vacío)'}</code></p>
                        {r.stderr && <p className="text-destructive">{r.stderr}</p>}
                      </div>
                    )}
                    {!r.paso && !r.es_publico && r.stderr && (
                      <p className="text-destructive">{r.stderr}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Modal de nota final combinada (teoría + práctica) */}
      <Dialog open={!!resultadoFinal} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-md [&>button]:hidden">
          <DialogHeader className="sr-only">
            <DialogTitle>Nota final del examen</DialogTitle>
          </DialogHeader>
          {resultadoFinal && (
            <div className="space-y-6 py-2">
              <div className="flex flex-col items-center gap-2">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <Trophy className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-2xl font-bold">Examen Completado</h2>
              </div>

              <div className="text-center">
                <p className="text-5xl font-bold text-primary">{resultadoFinal.nota.toFixed(1)}</p>
                <p className="text-sm text-muted-foreground">de 5.0 (nota final)</p>
              </div>

              <div className="flex justify-center gap-8 text-center">
                <div>
                  <p className="text-xl font-bold">{resultadoFinal.nota_teoria.toFixed(1)}</p>
                  <p className="text-xs text-muted-foreground">Teoría ({100 - resultadoFinal.peso_practica}%)</p>
                </div>
                <div>
                  <p className="text-xl font-bold">{resultadoFinal.nota_practica.toFixed(1)}</p>
                  <p className="text-xs text-muted-foreground">Práctica ({resultadoFinal.peso_practica}%)</p>
                </div>
              </div>

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
    </div>
  )
}
