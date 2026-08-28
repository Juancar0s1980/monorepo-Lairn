// Tab de laboratorios del curso (vista del docente): actividad práctica
// independiente del examen adaptativo, para CUALQUIER carrera — no solo
// programación. Cada laboratorio puede tener preguntas de código, respuesta
// abierta, problema con imagen o pronunciación (ver types/laboratorio.ts).
//
// Lista los laboratorios con creación y eliminación. Editar las preguntas
// pasa a la página dedicada /mis-cursos/{cursoId}/laboratorios/{id}.
//
// Endpoints: GET/POST /laboratorios/cursos/{cursoId}/laboratorios/,
//            DELETE /laboratorios/laboratorios/{laboratorioId}/.

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Check, Code2, ImageIcon, Loader2, Mic, NotebookPen, Plus, Sparkles, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { OPCIONES_LENGUAJE, OPCIONES_TIPO_PREGUNTA } from '@/types/laboratorio'
import type {
  Laboratorio,
  LenguajeCodigo,
  PreguntaDocente,
  PreguntaPayload,
  PreguntaLibreSugerida,
  RespuestaSugerirLaboratorioLibre,
  TipoPregunta,
} from '@/types/laboratorio'

interface TabLaboratoriosDocenteProps {
  cursoId: string
}

export function TabLaboratoriosDocente({ cursoId }: TabLaboratoriosDocenteProps) {
  const navigate = useNavigate()
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([])
  const [cargando, setCargando] = useState(true)

  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [titulo, setTitulo] = useState('')
  const [instrucciones, setInstrucciones] = useState('')
  const [creando, setCreando] = useState(false)

  // Generación de laboratorio completo con IA a partir de un enunciado libre.
  const [dialogoIaAbierto, setDialogoIaAbierto] = useState(false)
  const [enunciadoLibre, setEnunciadoLibre] = useState('')
  const [tipoLibre, setTipoLibre] = useState<TipoPregunta>('codigo')
  const [lenguajeLibre, setLenguajeLibre] = useState<LenguajeCodigo>('python')
  const [cantidadPreguntas, setCantidadPreguntas] = useState(3)
  const [generandoLibre, setGenerandoLibre] = useState(false)

  // Curación del borrador generado (segundo paso, mismo patrón que objetivos/preguntas por objetivo).
  const [dialogoCuracionAbierto, setDialogoCuracionAbierto] = useState(false)
  const [borrador, setBorrador] = useState<RespuestaSugerirLaboratorioLibre | null>(null)
  const [tituloBorrador, setTituloBorrador] = useState('')
  const [instruccionesBorrador, setInstruccionesBorrador] = useState('')
  const [seleccionadas, setSeleccionadas] = useState<Set<number>>(new Set())
  const [creandoDesdeBorrador, setCreandoDesdeBorrador] = useState(false)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<Laboratorio[]>(
          `/laboratorios/cursos/${cursoId}/laboratorios/`,
          { signal: controlador.signal }
        )
        setLaboratorios(data)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudieron cargar los laboratorios')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId])

  const crearLaboratorio = async () => {
    const tituloLimpio = titulo.trim()
    if (!tituloLimpio) return
    setCreando(true)
    try {
      const { data } = await api.post<Laboratorio>(
        `/laboratorios/cursos/${cursoId}/laboratorios/`,
        { titulo: tituloLimpio, instrucciones: instrucciones.trim() }
      )
      setLaboratorios((prev) => [data, ...prev])
      setDialogoAbierto(false)
      setTitulo('')
      setInstrucciones('')
      toast.success('Laboratorio creado')
      navigate(`/mis-cursos/${cursoId}/laboratorios/${data.id}`)
    } catch {
      toast.error('No se pudo crear el laboratorio')
    } finally {
      setCreando(false)
    }
  }

  const eliminarLaboratorio = async (id: number) => {
    try {
      await api.delete(`/laboratorios/laboratorios/${id}/`)
      setLaboratorios((prev) => prev.filter((l) => l.id !== id))
      toast.success('Laboratorio eliminado')
    } catch {
      toast.error('No se pudo eliminar el laboratorio')
    }
  }

  // Pide a la IA un laboratorio completo. Tarda (genera con IA y verifica cada
  // caso de test ejecutando la solución de referencia en el sandbox).
  const generarLaboratorioLibre = async () => {
    const texto = enunciadoLibre.trim()
    if (!texto) return
    setGenerandoLibre(true)
    try {
      const { data } = await api.post<RespuestaSugerirLaboratorioLibre>(
        `/laboratorios/cursos/${cursoId}/laboratorios/sugerir-libre/`,
        {
          enunciado: texto,
          tipo: tipoLibre,
          lenguaje: tipoLibre === 'codigo' ? lenguajeLibre : undefined,
          cantidad_preguntas: cantidadPreguntas,
        },
        { timeout: 300000 }
      )
      setBorrador(data)
      setTituloBorrador(data.titulo)
      setInstruccionesBorrador(data.instrucciones)
      setSeleccionadas(new Set(data.preguntas.map((_, i) => i)))
      setDialogoIaAbierto(false)
      setDialogoCuracionAbierto(true)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } }
      const data = axiosErr.response?.data
      const detalle = typeof data?.detalle === 'string' ? data.detalle : undefined
      // Errores de validación del serializer vienen como {campo: ["mensaje"]}, no como {detalle}.
      const mensajesCampos = data
        ? Object.values(data).flat().filter((v): v is string => typeof v === 'string')
        : []
      toast.error(detalle ?? (mensajesCampos.join('. ') || 'No se pudo generar el laboratorio con IA'))
    } finally {
      setGenerandoLibre(false)
    }
  }

  const alternarSeleccion = (i: number) => {
    setSeleccionadas((prev) => {
      const nuevo = new Set(prev)
      if (nuevo.has(i)) nuevo.delete(i)
      else nuevo.add(i)
      return nuevo
    })
  }

  // Crea el laboratorio real (POST normal) y dentro las preguntas marcadas (POST normal, una por una).
  const aceptarBorrador = async () => {
    if (!borrador) return
    const tituloFinal = tituloBorrador.trim()
    if (!tituloFinal) {
      toast.error('El título es obligatorio')
      return
    }
    const elegidas = borrador.preguntas.filter((_, i) => seleccionadas.has(i))
    if (elegidas.length === 0) {
      setDialogoCuracionAbierto(false)
      return
    }

    setCreandoDesdeBorrador(true)
    try {
      const { data: laboratorioCreado } = await api.post<Laboratorio>(
        `/laboratorios/cursos/${cursoId}/laboratorios/`,
        { titulo: tituloFinal, instrucciones: instruccionesBorrador.trim() }
      )

      for (const pregunta of elegidas as PreguntaLibreSugerida[]) {
        const payload: PreguntaPayload = {
          tipo: pregunta.tipo,
          enunciado: pregunta.enunciado,
          lenguaje: pregunta.lenguaje ?? 'python',
          codigo_inicial: pregunta.codigo_inicial ?? '',
          setup_sql: pregunta.setup_sql ?? '',
          criterios_ia: pregunta.criterios_ia,
          variantes_base64: pregunta.variantes,
          texto_pronunciar: pregunta.texto_pronunciar,
          puntos: pregunta.puntos,
          orden: pregunta.orden,
          casos_test: pregunta.casos_test,
        }
        await api.post<PreguntaDocente>(
          `/laboratorios/laboratorios/${laboratorioCreado.id}/preguntas/`,
          payload
        )
      }

      toast.success(`Laboratorio creado con ${elegidas.length} pregunta(s)`)
      setDialogoCuracionAbierto(false)
      navigate(`/mis-cursos/${cursoId}/laboratorios/${laboratorioCreado.id}`)
    } catch {
      toast.error('No se pudo crear el laboratorio a partir del borrador')
    } finally {
      setCreandoDesdeBorrador(false)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-[30vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground max-w-prose">
          Actividades prácticas independientes de los exámenes de opción múltiple: código, respuesta abierta, problema con imagen o pronunciación — para cualquier carrera.
        </p>
        <div className="flex shrink-0 gap-2">
          <Button variant="outline" onClick={() => setDialogoIaAbierto(true)}>
            <Sparkles className="h-4 w-4" />
            Generar con IA
          </Button>
          <Button onClick={() => setDialogoAbierto(true)}>
            <Plus className="h-4 w-4" />
            Nuevo laboratorio
          </Button>
        </div>
      </div>

      {laboratorios.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Code2 className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Este curso aún no tiene laboratorios
          </p>
          <p className="text-xs text-muted-foreground">
            Crea uno y agrega preguntas de código con sus casos de test
          </p>
        </div>
      )}

      {laboratorios.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {laboratorios.map((lab) => (
            <Card
              key={lab.id}
              className="cursor-pointer overflow-hidden transition-colors hover:border-primary/40"
              onClick={() => navigate(`/mis-cursos/${cursoId}/laboratorios/${lab.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm line-clamp-1">{lab.titulo}</CardTitle>
                  <Button
                    size="icon-sm"
                    variant="ghost"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    title="Eliminar"
                    onClick={(e) => {
                      e.stopPropagation()
                      eliminarLaboratorio(lab.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="line-clamp-2 text-xs text-muted-foreground">
                  {lab.instrucciones || 'Sin instrucciones adicionales'}
                </p>
                <Badge variant="outline" className="text-xs">
                  {lab.total_preguntas} pregunta{lab.total_preguntas === 1 ? '' : 's'}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogoAbierto} onOpenChange={(open) => !creando && setDialogoAbierto(open)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Code2 className="h-4 w-4 text-primary" />
              Nuevo laboratorio
            </DialogTitle>
            <DialogDescription>
              Después de crearlo podrás agregar preguntas de código, respuesta abierta, problema con imagen o pronunciación.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <Input
              placeholder="Título, ej: Lab 1: Fundamentos de Python"
              value={titulo}
              maxLength={200}
              onChange={(e) => setTitulo(e.target.value)}
              autoFocus
            />
            <Textarea
              placeholder="Instrucciones para el estudiante (opcional)"
              value={instrucciones}
              rows={3}
              onChange={(e) => setInstrucciones(e.target.value)}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogoAbierto(false)} disabled={creando}>
              Cancelar
            </Button>
            <Button onClick={crearLaboratorio} disabled={creando || !titulo.trim()}>
              {creando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear y editar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Diálogo de generación libre con IA (paso 1: describir el laboratorio) */}
      <Dialog open={dialogoIaAbierto} onOpenChange={(open) => !generandoLibre && setDialogoIaAbierto(open)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Generar laboratorio con IA
            </DialogTitle>
            <DialogDescription>
              Describe qué laboratorio quieres y elige el tipo de ejercicio. La IA genera título,
              instrucciones y las preguntas
              {tipoLibre === 'codigo' && ' — cada caso de test se verifica ejecutando una solución de referencia real en el sandbox'}
              . Puede tardar uno o dos minutos.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Tipo de laboratorio</Label>
              <div className="flex gap-2">
                {OPCIONES_TIPO_PREGUNTA.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setTipoLibre(o.value)}
                    className={`flex-1 rounded-lg border px-2 py-2 text-xs transition-colors ${
                      tipoLibre === o.value
                        ? 'border-primary bg-primary/5 text-foreground'
                        : 'border-border text-muted-foreground hover:bg-muted'
                    }`}
                  >
                    {o.value === 'codigo' ? (
                      <Code2 className="mr-1 inline h-3.5 w-3.5" />
                    ) : o.value === 'respuesta_libre' ? (
                      <NotebookPen className="mr-1 inline h-3.5 w-3.5" />
                    ) : o.value === 'problema_visual' ? (
                      <ImageIcon className="mr-1 inline h-3.5 w-3.5" />
                    ) : (
                      <Mic className="mr-1 inline h-3.5 w-3.5" />
                    )}
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Describe el laboratorio</Label>
              <Textarea
                placeholder={
                  tipoLibre === 'codigo'
                    ? 'Ej: un laboratorio de estructuras de datos con listas enlazadas, de dificultad media.'
                    : tipoLibre === 'respuesta_libre'
                      ? 'Ej: un laboratorio de inglés de negocios sobre cómo escribir correos formales.'
                      : tipoLibre === 'problema_visual'
                        ? 'Ej: un laboratorio de mecánica de fluidos sobre redes de tuberías en serie.'
                        : 'Ej: un laboratorio de pronunciación de vocabulario técnico de redes de computadoras.'
                }
                rows={3}
                value={enunciadoLibre}
                onChange={(e) => setEnunciadoLibre(e.target.value)}
                autoFocus
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {tipoLibre === 'codigo' && (
                <div className="space-y-1.5">
                  <Label>Lenguaje</Label>
                  <Select
                    items={OPCIONES_LENGUAJE}
                    value={lenguajeLibre}
                    onValueChange={(valor) => valor && setLenguajeLibre(valor as LenguajeCodigo)}
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
              )}
              <div className="space-y-1.5">
                <Label>Cantidad de preguntas (máximo 8)</Label>
                <Input
                  type="number"
                  min={1}
                  max={8}
                  value={cantidadPreguntas}
                  onChange={(e) => setCantidadPreguntas(Math.min(8, Math.max(1, Number(e.target.value) || 1)))}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogoIaAbierto(false)} disabled={generandoLibre}>
              Cancelar
            </Button>
            <Button onClick={generarLaboratorioLibre} disabled={generandoLibre || !enunciadoLibre.trim()}>
              {generandoLibre ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generando...
                </>
              ) : (
                'Generar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Diálogo de curación del borrador (paso 2: revisar y aceptar) */}
      <Dialog open={dialogoCuracionAbierto} onOpenChange={(open) => !creandoDesdeBorrador && setDialogoCuracionAbierto(open)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Revisa el laboratorio generado
            </DialogTitle>
            <DialogDescription>
              {tipoLibre === 'codigo'
                ? 'Los casos de test ya se verificaron ejecutando una solución de referencia real en el sandbox.'
                : tipoLibre === 'problema_visual'
                  ? 'Cada pregunta es un problema independiente, con sus propias variantes (diagrama + 4 opciones cada una).'
                  : tipoLibre === 'pronunciacion'
                    ? 'El audio de referencia de cada frase se genera al aceptar el borrador.'
                    : 'Cada pregunta incluye la rúbrica que usará la IA para calificar las respuestas de los estudiantes.'}{' '}
              Ajusta el título/instrucciones si quieres y marca las preguntas que quieras agregar.
            </DialogDescription>
          </DialogHeader>

          <div className="max-h-[55vh] space-y-3 overflow-y-auto">
            <div className="space-y-1.5">
              <Label>Título</Label>
              <Input value={tituloBorrador} maxLength={200} onChange={(e) => setTituloBorrador(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Instrucciones</Label>
              <Textarea rows={2} value={instruccionesBorrador} onChange={(e) => setInstruccionesBorrador(e.target.value)} />
            </div>

            <div className="space-y-2">
              {borrador?.preguntas.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => alternarSeleccion(i)}
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
                  <div className="flex-1 space-y-1.5">
                    <p className="text-foreground">{p.enunciado}</p>
                    {p.tipo === 'codigo' ? (
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] uppercase">{p.lenguaje}</Badge>
                        <span className="text-xs text-muted-foreground">{p.casos_test.length} caso(s) de test verificados</span>
                      </div>
                    ) : p.tipo === 'problema_visual' ? (
                      p.variantes && p.variantes.length > 0 && (
                        <div className="flex gap-2 overflow-x-auto pb-1">
                          {p.variantes.map((v, vi) => (
                            <img
                              key={vi}
                              src={`data:image/svg+xml;base64,${v.imagen_base64}`}
                              alt={`Variante ${vi + 1}`}
                              className="h-16 w-16 shrink-0 rounded border object-cover"
                            />
                          ))}
                          <span className="self-center text-xs text-muted-foreground">{p.variantes.length} variante(s)</span>
                        </div>
                      )
                    ) : p.tipo === 'pronunciacion' ? (
                      <div className="flex items-center gap-1.5">
                        <Mic className="h-3.5 w-3.5 text-muted-foreground" />
                        <Badge variant="outline" className="text-[10px]">{p.texto_pronunciar}</Badge>
                      </div>
                    ) : (
                      <p className="line-clamp-2 text-xs text-muted-foreground">Rúbrica: {p.criterios_ia}</p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogoCuracionAbierto(false)} disabled={creandoDesdeBorrador}>
              Descartar
            </Button>
            <Button onClick={aceptarBorrador} disabled={creandoDesdeBorrador || seleccionadas.size === 0 || !tituloBorrador.trim()}>
              {creandoDesdeBorrador ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creando...
                </>
              ) : (
                `Crear laboratorio con ${seleccionadas.size} pregunta(s)`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
