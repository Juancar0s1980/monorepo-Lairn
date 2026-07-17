// Resolución de un laboratorio de código, para el rol Estudiante.
//
// Layout tipo "juez en línea" (LeetCode): enunciado + ejemplos a la
// izquierda, editor de código + resultado de ejecución a la derecha.
// El botón "Ejecutar" corre el código contra los casos de test PÚBLICOS en
// el sandbox del microservicio ejecutor — no guarda nada (ver
// vista_ejecutar_codigo.py). El envío calificado con tests ocultos + IA
// es la Fase 4, todavía no implementada.

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '@/services/api'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { EditorCodigo } from '@/components/editor-codigo'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { CheckCircle2, Clock, Code2, Loader2, Play, Send, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import type { LaboratorioDetalleEstudiante, MisEntregas, ResultadoEjecucion, ResultadoEnvio } from '@/types/laboratorio'

// Formatea un ISO a fecha/hora legible en español.
function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
}

export default function PaginaResolverLaboratorioEstudiante() {
  const { cursoId, laboratorioId } = useParams<{ cursoId: string; laboratorioId: string }>()

  const [laboratorio, setLaboratorio] = useState<LaboratorioDetalleEstudiante | null>(null)
  const [cargando, setCargando] = useState(true)
  const [indiceActivo, setIndiceActivo] = useState(0)

  // Código por pregunta (id -> código actual), para no perder progreso al cambiar de pregunta.
  const [codigos, setCodigos] = useState<Record<number, string>>({})
  const [ejecutando, setEjecutando] = useState(false)
  const [resultado, setResultado] = useState<ResultadoEjecucion | null>(null)

  const [enviando, setEnviando] = useState(false)
  const [resultadoEnvio, setResultadoEnvio] = useState<ResultadoEnvio | null>(null)
  const [misEntregas, setMisEntregas] = useState<MisEntregas | null>(null)

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
        setCodigos(inicial)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudo cargar el laboratorio')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId, laboratorioId])

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

  const ejecutar = async () => {
    setEjecutando(true)
    setResultado(null)
    setResultadoEnvio(null)
    try {
      const { data } = await api.post<ResultadoEjecucion>(
        `/laboratorios/preguntas/${pregunta.id}/ejecutar/`,
        { codigo: codigos[pregunta.id] ?? '' }
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
    setEnviando(true)
    setResultado(null)
    setResultadoEnvio(null)
    try {
      const { data } = await api.post<ResultadoEnvio>(
        `/laboratorios/preguntas/${pregunta.id}/enviar/`,
        { codigo: codigos[pregunta.id] ?? '' }
      )
      setResultadoEnvio(data)
      setMisEntregas((prev) =>
        prev
          ? {
              ...prev,
              intentos_usados: prev.intentos_usados + 1,
              intentos_restantes: data.intentos_restantes,
              entregas: [...prev.entregas, {
                id: data.id, intento: data.intento, casos_pasados: data.casos_pasados,
                casos_totales: data.casos_totales, puntaje: data.puntaje, enviado_en: data.enviado_en,
              }],
            }
          : prev
      )
      toast.success(`Enviado: ${data.puntaje}% (${data.casos_pasados}/${data.casos_totales} casos)`)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudo enviar el código')
    } finally {
      setEnviando(false)
    }
  }

  const cambiarPregunta = (indice: number) => {
    setIndiceActivo(indice)
    setResultado(null)
    setResultadoEnvio(null)
  }

  const sinIntentos = misEntregas?.intentos_restantes === 0
  const fechaLimiteSuperada = !!(laboratorio && misEntregas?.fecha_limite && new Date(misEntregas.fecha_limite) < new Date())

  return (
    <div className="space-y-4">
      <EncabezadoGradiente
        titulo={laboratorio.titulo}
        subtitulo={laboratorio.instrucciones || 'Resuelve las preguntas de código'}
        volverA={`/mis-cursos/${cursoId}/examenes`}
        volverTexto="Volver al curso"
      />

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
        {/* Panel izquierdo: enunciado + ejemplos */}
        <Card>
          <CardContent className="space-y-4 pt-5">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="uppercase">{pregunta.lenguaje}</Badge>
              <Badge variant="secondary">{pregunta.puntos} pts</Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm">{pregunta.enunciado}</p>

            {pregunta.lenguaje === 'sql' && pregunta.setup_sql && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Esquema</p>
                <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-xs">{pregunta.setup_sql}</pre>
              </div>
            )}

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
          </CardContent>
        </Card>

        {/* Panel derecho: editor + ejecutar + resultado */}
        <Card>
          <CardContent className="space-y-3 pt-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tu solución</p>
              <div className="flex items-center gap-2">
                {misEntregas && (
                  <Badge variant="outline" className="text-xs">
                    {misEntregas.max_intentos
                      ? `${misEntregas.intentos_usados}/${misEntregas.max_intentos} intentos`
                      : `${misEntregas.intentos_usados} intento(s)`}
                  </Badge>
                )}
                <Button size="sm" variant="outline" onClick={ejecutar} disabled={ejecutando}>
                  {ejecutando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                  Ejecutar
                </Button>
                <Button
                  size="sm"
                  onClick={enviar}
                  disabled={enviando || sinIntentos || fechaLimiteSuperada}
                  title={
                    sinIntentos
                      ? 'Ya usaste todos tus intentos para esta pregunta'
                      : fechaLimiteSuperada
                        ? 'La fecha límite ya pasó'
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

            <EditorCodigo
              lenguaje={pregunta.lenguaje}
              valor={codigos[pregunta.id] ?? ''}
              onChange={(valor) => setCodigos((prev) => ({ ...prev, [pregunta.id]: valor }))}
              altura="280px"
            />

            {/* Resultado de la ejecución */}
            {resultado && (
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
                    {resultadoEnvio.puntaje}% · {resultadoEnvio.casos_pasados}/{resultadoEnvio.casos_totales} casos
                  </Badge>
                </div>
                {resultadoEnvio.resultados.map((r, i) => (
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
    </div>
  )
}
