// Editor de un laboratorio de código, para el rol Docente.
//
// Layout tipo "juez en línea": lista de preguntas a la izquierda, formulario
// de edición (enunciado, código inicial/setup SQL, casos de test) a la
// derecha. Cada pregunta se guarda completa (incluidos sus casos de test)
// con un único POST/PATCH — ver serializador_pregunta_codigo.py en backend.

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '@/services/api'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { EditorCodigo } from '@/components/editor-codigo'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { BarChart3, Check, Code2, ListChecks, Loader2, Plus, Settings, Sparkles, Trash2, Users } from 'lucide-react'
import { toast } from 'sonner'
import { OPCIONES_LENGUAJE } from '@/types/laboratorio'
import type {
  LaboratorioDetalleDocente,
  PreguntaCodigoDocente,
  PreguntaCodigoPayload,
  PreguntaCodigoSugerida,
  RespuestaSugerirPreguntasCodigo,
  AnaliticaLaboratorio,
  LenguajeCodigo,
} from '@/types/laboratorio'

// Caso de test en edición local: `clave` es solo para el key de React y el
// remove, nunca se manda al backend (el POST/PATCH reemplaza el conjunto
// completo de casos, no hace falta id).
interface CasoEdicion {
  clave: number
  entrada: string
  salida_esperada: string
  es_publico: boolean
  orden: number
}

let contadorClaves = 0
const nuevaClave = () => ++contadorClaves

function casosDesdeApi(pregunta: PreguntaCodigoDocente): CasoEdicion[] {
  return pregunta.casos_test.map((c) => ({ ...c, clave: nuevaClave() }))
}

// Convierte un ISO (respuesta del backend) al formato que espera <input type="datetime-local">.
function isoAFechaLocal(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Convierte el valor de <input type="datetime-local"> a ISO para el backend, o null si está vacío.
function fechaLocalAIso(local: string): string | null {
  return local ? new Date(local).toISOString() : null
}

const FORM_VACIO = {
  enunciado: '',
  lenguaje: 'python' as LenguajeCodigo,
  codigo_inicial: '',
  setup_sql: '',
  criterios_ia: '',
  puntos: 100,
}

export default function PaginaEditorLaboratorioDocente() {
  const { cursoId, laboratorioId } = useParams<{ cursoId: string; laboratorioId: string }>()

  const [laboratorio, setLaboratorio] = useState<LaboratorioDetalleDocente | null>(null)
  const [cargando, setCargando] = useState(true)

  // Pregunta seleccionada: id existente, 'nueva', o null (nada seleccionado).
  const [seleccion, setSeleccion] = useState<number | 'nueva' | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [casos, setCasos] = useState<CasoEdicion[]>([])
  const [guardando, setGuardando] = useState(false)

  // Sugerencias de IA (una por objetivo del curso, con casos de test ya verificados en el sandbox).
  const [modalIaAbierto, setModalIaAbierto] = useState(false)
  const [generandoIa, setGenerandoIa] = useState(false)
  const [sugerencias, setSugerencias] = useState<PreguntaCodigoSugerida[]>([])
  const [objetivosSinGenerar, setObjetivosSinGenerar] = useState<string[]>([])
  const [seleccionadas, setSeleccionadas] = useState<Set<number>>(new Set())
  const [aceptandoIa, setAceptandoIa] = useState(false)

  // Configuración del laboratorio: intentos permitidos por pregunta y fecha límite de entrega.
  const [configMaxIntentos, setConfigMaxIntentos] = useState(0)
  const [configFechaLimite, setConfigFechaLimite] = useState('')
  const [guardandoConfig, setGuardandoConfig] = useState(false)

  // Analítica del laboratorio (se carga la primera vez que se abre esa tab).
  const [analitica, setAnalitica] = useState<AnaliticaLaboratorio | null>(null)
  const [cargandoAnalitica, setCargandoAnalitica] = useState(false)

  useEffect(() => {
    if (!laboratorioId) return
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<LaboratorioDetalleDocente>(
          `/laboratorios/laboratorios/${laboratorioId}/`,
          { signal: controlador.signal }
        )
        setLaboratorio(data)
        setConfigMaxIntentos(data.max_intentos)
        setConfigFechaLimite(isoAFechaLocal(data.fecha_limite))
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudo cargar el laboratorio')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [laboratorioId])

  const seleccionarPregunta = (pregunta: PreguntaCodigoDocente) => {
    setSeleccion(pregunta.id)
    setForm({
      enunciado: pregunta.enunciado,
      lenguaje: pregunta.lenguaje,
      codigo_inicial: pregunta.codigo_inicial,
      setup_sql: pregunta.setup_sql,
      criterios_ia: pregunta.criterios_ia,
      puntos: pregunta.puntos,
    })
    setCasos(casosDesdeApi(pregunta))
  }

  const nuevaPregunta = () => {
    setSeleccion('nueva')
    setForm(FORM_VACIO)
    setCasos([])
  }

  const agregarCaso = () => {
    setCasos((prev) => [
      ...prev,
      { clave: nuevaClave(), entrada: '', salida_esperada: '', es_publico: true, orden: prev.length + 1 },
    ])
  }

  const actualizarCaso = (clave: number, cambios: Partial<CasoEdicion>) => {
    setCasos((prev) => prev.map((c) => (c.clave === clave ? { ...c, ...cambios } : c)))
  }

  const eliminarCaso = (clave: number) => {
    setCasos((prev) => prev.filter((c) => c.clave !== clave))
  }

  const guardarPregunta = async () => {
    if (!laboratorio) return
    const enunciado = form.enunciado.trim()
    if (!enunciado) {
      toast.error('El enunciado es obligatorio')
      return
    }

    const payload: PreguntaCodigoPayload = {
      enunciado,
      lenguaje: form.lenguaje,
      codigo_inicial: form.codigo_inicial,
      setup_sql: form.setup_sql,
      criterios_ia: form.criterios_ia,
      puntos: form.puntos,
      orden: laboratorio.preguntas.length,
      casos_test: casos.map(({ entrada, salida_esperada, es_publico, orden }) => ({
        entrada,
        salida_esperada,
        es_publico,
        orden,
      })),
    }

    setGuardando(true)
    try {
      if (seleccion === 'nueva') {
        const { data } = await api.post<PreguntaCodigoDocente>(
          `/laboratorios/laboratorios/${laboratorioId}/preguntas/`,
          payload
        )
        setLaboratorio((prev) => (prev ? { ...prev, preguntas: [...prev.preguntas, data] } : prev))
        seleccionarPregunta(data)
        toast.success('Pregunta creada')
      } else if (seleccion !== null) {
        const { data } = await api.patch<PreguntaCodigoDocente>(
          `/laboratorios/preguntas/${seleccion}/`,
          payload
        )
        setLaboratorio((prev) =>
          prev ? { ...prev, preguntas: prev.preguntas.map((p) => (p.id === data.id ? data : p)) } : prev
        )
        seleccionarPregunta(data)
        toast.success('Pregunta actualizada')
      }
    } catch {
      toast.error('No se pudo guardar la pregunta')
    } finally {
      setGuardando(false)
    }
  }

  const eliminarPreguntaActual = async () => {
    if (typeof seleccion !== 'number') return
    try {
      await api.delete(`/laboratorios/preguntas/${seleccion}/`)
      setLaboratorio((prev) =>
        prev ? { ...prev, preguntas: prev.preguntas.filter((p) => p.id !== seleccion) } : prev
      )
      setSeleccion(null)
      toast.success('Pregunta eliminada')
    } catch {
      toast.error('No se pudo eliminar la pregunta')
    }
  }

  // Pide a la IA un borrador por cada objetivo del curso. Tarda (genera con IA
  // y luego ejecuta la solución de referencia de cada caso en el sandbox para
  // verificar la salida real), así que puede tomar uno o dos minutos.
  const pedirSugerenciasIa = async () => {
    if (!laboratorioId) return
    setGenerandoIa(true)
    try {
      const { data } = await api.post<RespuestaSugerirPreguntasCodigo>(
        `/laboratorios/laboratorios/${laboratorioId}/preguntas/sugerir-ia/`,
        {},
        { timeout: 300000 }
      )
      setSugerencias(data.preguntas)
      setObjetivosSinGenerar(data.objetivos_sin_generar)
      setSeleccionadas(new Set(data.preguntas.map((_, i) => i)))
      setModalIaAbierto(true)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudieron generar preguntas con IA')
    } finally {
      setGenerandoIa(false)
    }
  }

  const alternarSeleccionIa = (i: number) => {
    setSeleccionadas((prev) => {
      const nuevo = new Set(prev)
      if (nuevo.has(i)) nuevo.delete(i)
      else nuevo.add(i)
      return nuevo
    })
  }

  // Crea como preguntas reales (POST normal) solo las sugerencias marcadas.
  const aceptarSugerenciasIa = async () => {
    if (!laboratorioId || !laboratorio) return
    const elegidas = sugerencias.filter((_, i) => seleccionadas.has(i))
    if (elegidas.length === 0) {
      setModalIaAbierto(false)
      return
    }
    setAceptandoIa(true)
    try {
      const creadas: PreguntaCodigoDocente[] = []
      for (const sugerencia of elegidas) {
        const payload: PreguntaCodigoPayload = {
          enunciado: sugerencia.enunciado,
          lenguaje: sugerencia.lenguaje,
          codigo_inicial: sugerencia.codigo_inicial,
          setup_sql: sugerencia.setup_sql,
          criterios_ia: sugerencia.criterios_ia,
          puntos: sugerencia.puntos,
          orden: laboratorio.preguntas.length + creadas.length,
          casos_test: sugerencia.casos_test,
        }
        const { data } = await api.post<PreguntaCodigoDocente>(
          `/laboratorios/laboratorios/${laboratorioId}/preguntas/`,
          payload
        )
        creadas.push(data)
      }
      setLaboratorio((prev) => (prev ? { ...prev, preguntas: [...prev.preguntas, ...creadas] } : prev))
      toast.success(`${creadas.length} pregunta(s) agregada(s)`)
      setModalIaAbierto(false)
    } catch {
      toast.error('No se pudieron guardar todas las preguntas sugeridas')
    } finally {
      setAceptandoIa(false)
    }
  }

  const guardarConfiguracion = async () => {
    if (!laboratorioId) return
    setGuardandoConfig(true)
    try {
      const { data } = await api.patch<LaboratorioDetalleDocente>(
        `/laboratorios/laboratorios/${laboratorioId}/`,
        { max_intentos: configMaxIntentos, fecha_limite: fechaLocalAIso(configFechaLimite) }
      )
      setLaboratorio((prev) => (prev ? { ...prev, max_intentos: data.max_intentos, fecha_limite: data.fecha_limite } : prev))
      toast.success('Configuración guardada')
    } catch {
      toast.error('No se pudo guardar la configuración')
    } finally {
      setGuardandoConfig(false)
    }
  }

  const cargarAnalitica = async () => {
    if (!laboratorioId || analitica) return
    setCargandoAnalitica(true)
    try {
      const { data } = await api.get<AnaliticaLaboratorio>(`/laboratorios/laboratorios/${laboratorioId}/analitica/`)
      setAnalitica(data)
    } catch {
      toast.error('No se pudo cargar la analítica')
    } finally {
      setCargandoAnalitica(false)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!laboratorio) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-2 text-center">
        <Code2 className="h-10 w-10 text-muted-foreground/50" />
        <p className="text-sm font-medium text-muted-foreground">Laboratorio no encontrado</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <EncabezadoGradiente
        titulo={laboratorio.titulo}
        subtitulo="Editor de laboratorio de código"
        volverA={`/mis-cursos/${cursoId}/examenes`}
        volverTexto="Volver al curso"
        badgeTexto={`${laboratorio.preguntas.length} pregunta(s)`}
      />

      <Tabs defaultValue="preguntas" onValueChange={(valor) => valor === 'analitica' && cargarAnalitica()}>
        <TabsList>
          <TabsTrigger value="preguntas">
            <ListChecks className="h-4 w-4" />
            Preguntas
          </TabsTrigger>
          <TabsTrigger value="configuracion">
            <Settings className="h-4 w-4" />
            Configuración
          </TabsTrigger>
          <TabsTrigger value="analitica">
            <BarChart3 className="h-4 w-4" />
            Analítica
          </TabsTrigger>
        </TabsList>

        <TabsContent value="preguntas" className="space-y-4 pt-4">
      <div className="flex justify-end">
        <Button variant="outline" onClick={pedirSugerenciasIa} disabled={generandoIa}>
          {generandoIa ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generando y verificando... (puede tardar 1-2 min)
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generar con IA a partir de los objetivos
            </>
          )}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        {/* Lista de preguntas */}
        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Preguntas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 p-2 pt-0">
            {laboratorio.preguntas.map((pregunta, indice) => (
              <button
                key={pregunta.id}
                type="button"
                onClick={() => seleccionarPregunta(pregunta)}
                className={`flex w-full items-start gap-2 rounded-lg border p-2.5 text-left text-xs transition-colors ${
                  seleccion === pregunta.id
                    ? 'border-primary bg-primary/5'
                    : 'border-transparent hover:bg-muted'
                }`}
              >
                <span className="shrink-0 font-semibold text-muted-foreground">{indice + 1}.</span>
                <span className="flex-1 line-clamp-2">{pregunta.enunciado}</span>
                <Badge variant="outline" className="shrink-0 text-[10px] uppercase">
                  {pregunta.lenguaje}
                </Badge>
              </button>
            ))}
            <Button variant="outline" size="sm" className="w-full" onClick={nuevaPregunta}>
              <Plus className="h-3.5 w-3.5" />
              Nueva pregunta
            </Button>
          </CardContent>
        </Card>

        {/* Formulario de edición */}
        {seleccion === null ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <Code2 className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              Selecciona una pregunta o crea una nueva
            </p>
          </div>
        ) : (
          <Card>
            <CardContent className="space-y-4 pt-5">
              <div className="space-y-1.5">
                <Label>Enunciado *</Label>
                <Textarea
                  rows={3}
                  placeholder="Ej: Lee un entero por stdin e imprime su doble."
                  value={form.enunciado}
                  onChange={(e) => setForm((f) => ({ ...f, enunciado: e.target.value }))}
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Lenguaje</Label>
                  <Select
                    items={OPCIONES_LENGUAJE}
                    value={form.lenguaje}
                    onValueChange={(valor) =>
                      valor && setForm((f) => ({ ...f, lenguaje: valor as LenguajeCodigo }))
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      {OPCIONES_LENGUAJE.map((o) => (
                        <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Puntos</Label>
                  <Input
                    type="number"
                    min={1}
                    value={form.puntos}
                    onChange={(e) => setForm((f) => ({ ...f, puntos: Number(e.target.value) || 0 }))}
                  />
                </div>
              </div>

              {form.lenguaje !== 'sql' ? (
                <div className="space-y-1.5">
                  <Label>
                    Código inicial (plantilla que ve el estudiante)
                    {form.lenguaje === 'java' && ' — la clase pública debe llamarse "Main"'}
                  </Label>
                  <EditorCodigo
                    lenguaje={form.lenguaje}
                    valor={form.codigo_inicial}
                    onChange={(valor) => setForm((f) => ({ ...f, codigo_inicial: valor }))}
                    altura="180px"
                  />
                </div>
              ) : (
                <div className="space-y-1.5">
                  <Label>Setup SQL (esquema + datos semilla, corre antes de la consulta del estudiante)</Label>
                  <EditorCodigo
                    lenguaje="sql"
                    valor={form.setup_sql}
                    onChange={(valor) => setForm((f) => ({ ...f, setup_sql: valor }))}
                    altura="180px"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <Label>Criterios para evaluación por IA (opcional)</Label>
                <Textarea
                  rows={2}
                  placeholder="Ej: valora legibilidad y que no use variables globales innecesarias."
                  value={form.criterios_ia}
                  onChange={(e) => setForm((f) => ({ ...f, criterios_ia: e.target.value }))}
                />
              </div>

              {/* Casos de test */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Casos de test</Label>
                  <Button variant="outline" size="sm" onClick={agregarCaso}>
                    <Plus className="h-3.5 w-3.5" />
                    Agregar caso
                  </Button>
                </div>

                {casos.length === 0 && (
                  <p className="text-xs text-muted-foreground">Sin casos de test todavía.</p>
                )}

                {casos.map((caso, indice) => (
                  <div key={caso.clave} className="space-y-2 rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={caso.es_publico}
                          onCheckedChange={(valor) => actualizarCaso(caso.clave, { es_publico: valor })}
                        />
                        <span className="text-xs text-muted-foreground">
                          {caso.es_publico ? `Caso ${indice + 1} · público (ejemplo)` : `Caso ${indice + 1} · oculto (solo calificación)`}
                        </span>
                      </div>
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => eliminarCaso(caso.clave)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">
                          {form.lenguaje !== 'sql' ? 'Entrada (stdin)' : 'SQL adicional para este caso (opcional)'}
                        </Label>
                        <Textarea
                          rows={2}
                          value={caso.entrada}
                          onChange={(e) => actualizarCaso(caso.clave, { entrada: e.target.value })}
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">
                          {form.lenguaje !== 'sql'
                            ? 'Salida esperada (stdout exacto)'
                            : 'Filas esperadas, ej: [[3]]'}
                        </Label>
                        <Textarea
                          rows={2}
                          value={caso.salida_esperada}
                          onChange={(e) => actualizarCaso(caso.clave, { salida_esperada: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between border-t pt-4">
                {typeof seleccion === 'number' ? (
                  <Button variant="destructive" onClick={eliminarPreguntaActual}>
                    <Trash2 className="h-4 w-4" />
                    Eliminar pregunta
                  </Button>
                ) : (
                  <span />
                )}
                <Button onClick={guardarPregunta} disabled={guardando || !form.enunciado.trim()}>
                  {guardando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Guardar'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
        </TabsContent>

        <TabsContent value="configuracion" className="pt-4">
          <Card className="sm:max-w-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Configuración del laboratorio</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label>Intentos permitidos por pregunta</Label>
                <Input
                  type="number"
                  min={0}
                  value={configMaxIntentos}
                  onChange={(e) => setConfigMaxIntentos(Number(e.target.value) || 0)}
                />
                <p className="text-xs text-muted-foreground">0 = intentos ilimitados.</p>
              </div>
              <div className="space-y-1.5">
                <Label>Fecha límite de entrega</Label>
                <Input
                  type="datetime-local"
                  value={configFechaLimite}
                  onChange={(e) => setConfigFechaLimite(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Vacío = sin límite. Después de esta fecha, el estudiante ya no puede enviar (pero sí puede seguir usando "Ejecutar").
                </p>
              </div>
              <Button onClick={guardarConfiguracion} disabled={guardandoConfig}>
                {guardandoConfig ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Guardar configuración'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analitica" className="pt-4">
          {cargandoAnalitica ? (
            <div className="flex h-[30vh] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !analitica || analitica.total_estudiantes_intentaron === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
              <BarChart3 className="h-10 w-10 text-muted-foreground/50" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">Todavía no hay entregas</p>
              <p className="text-xs text-muted-foreground">Los datos aparecerán cuando los estudiantes envíen soluciones</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{analitica.total_estudiantes_intentaron}</span> estudiante(s) han intentado este laboratorio.
              </p>

              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Por pregunta</h3>
                {analitica.preguntas.map((p) => (
                  <Card key={p.pregunta_id}>
                    <CardContent className="space-y-2 pt-4">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm">{p.enunciado}</p>
                        <Badge variant="outline" className="shrink-0 text-[10px] uppercase">{p.lenguaje}</Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><Users className="h-3 w-3" />{p.estudiantes_resueltas}/{p.estudiantes_intentaron} la resolvieron</span>
                        {p.porcentaje_acierto_promedio !== null && <span>{p.porcentaje_acierto_promedio}% acierto promedio</span>}
                        {p.intentos_promedio !== null && <span>{p.intentos_promedio} intentos promedio</span>}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Por estudiante</h3>
                <Card>
                  <CardContent className="divide-y p-0">
                    {analitica.estudiantes.map((e) => (
                      <div key={e.estudiante_id} className="flex items-center justify-between gap-3 px-4 py-3">
                        <div>
                          <p className="text-sm font-medium">{e.nombre}</p>
                          <p className="text-xs text-muted-foreground">{e.email}</p>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <Badge variant="outline">{e.preguntas_resueltas}/{e.total_preguntas} resueltas</Badge>
                          <span className="font-semibold">{e.puntaje_promedio}%</span>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Modal de curación de sugerencias de IA */}
      <Dialog open={modalIaAbierto} onOpenChange={(open) => !aceptandoIa && setModalIaAbierto(open)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Preguntas sugeridas por IA
            </DialogTitle>
            <DialogDescription>
              Una por objetivo del curso. Los casos de test ya se verificaron ejecutando una
              solución de referencia en el sandbox, no son un cálculo a mano de la IA. Marca las
              que quieras agregar.
            </DialogDescription>
          </DialogHeader>

          <div className="max-h-[50vh] space-y-2 overflow-y-auto">
            {objetivosSinGenerar.length > 0 && (
              <p className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400">
                No se pudo generar una pregunta verificable para: {objetivosSinGenerar.join('; ')}
              </p>
            )}

            {sugerencias.map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => alternarSeleccionIa(i)}
                className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left text-sm transition-colors ${
                  seleccionadas.has(i)
                    ? 'border-primary bg-primary/5'
                    : 'border-border text-muted-foreground'
                }`}
              >
                <span
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                    seleccionadas.has(i) ? 'border-primary bg-primary text-primary-foreground' : 'border-input'
                  }`}
                >
                  {seleccionadas.has(i) && <Check className="h-3 w-3" />}
                </span>
                <div className="flex-1 space-y-1">
                  <p className="text-xs text-muted-foreground">Objetivo: {s.objetivo}</p>
                  <p className="text-foreground">{s.enunciado}</p>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px] uppercase">{s.lenguaje}</Badge>
                    <span className="text-xs text-muted-foreground">{s.casos_test.length} caso(s) de test verificados</span>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalIaAbierto(false)} disabled={aceptandoIa}>
              Descartar
            </Button>
            <Button onClick={aceptarSugerenciasIa} disabled={aceptandoIa || seleccionadas.size === 0}>
              {aceptandoIa ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                `Agregar ${seleccionadas.size} pregunta(s)`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
