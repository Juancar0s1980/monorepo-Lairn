// Llamado a lista del docente supervisor (ADR-009).
//
// - Lista de todos los convocados con buscador y filtro por estado.
// - Por estudiante: Presente / Tarde / Ausente / Excusa (diálogo con tipo de
//   excusa y observación). Solo presente y tarde habilitan iniciar el intento.
// - "Marcar todos presentes" (con confirmación) marca a los que no se han llamado.
// - Columna de progreso del intento (sin nota) y refresco cada 10 s.
// - Integridad (ADR-010): distintivo "Suspendido", incidentes con hora y tipo,
//   y decisión Reactivar / Anular por fraude con motivo obligatorio.

import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '@/services/api'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { ArrowLeft, CheckCheck, Loader2, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EstadoAsistencia, FilaSeguimiento, Seguimiento, TipoExcusa } from '@/types/supervision'
import { mensajeError } from '@/pages/academico/academico-utils'
import { ChipAsistencia, ProgresoIntento, TarjetasConteo } from './componentes-supervision'
import { ChipIntegridad, PanelIntegridad } from './integridad-supervision'
import {
  ETIQUETA_ASISTENCIA,
  ETIQUETA_EXCUSA,
  formatoFecha,
  formatoHora,
  useConsultaPeriodica,
  useRelojServidor,
} from './supervision-utils'

type Filtro = 'todos' | 'sin_llamar' | 'suspendido' | EstadoAsistencia
const FILTROS: { valor: Filtro; texto: string }[] = [
  { valor: 'todos', texto: 'Todos' },
  { valor: 'sin_llamar', texto: 'Sin llamar' },
  { valor: 'presente', texto: 'Presentes' },
  { valor: 'tarde', texto: 'Tarde' },
  { valor: 'ausente', texto: 'Ausentes' },
  { valor: 'excusa', texto: 'Excusa' },
  { valor: 'suspendido', texto: 'Suspendidos' },
]
const BOTONES: { estado: EstadoAsistencia; activo: string }[] = [
  { estado: 'presente', activo: 'border-success bg-success/10 text-success' },
  { estado: 'tarde', activo: 'border-warning bg-warning/15 text-foreground' },
  { estado: 'ausente', activo: 'border-destructive bg-destructive/10 text-destructive' },
  { estado: 'excusa', activo: 'border-primary bg-primary/10 text-primary' },
]
const TIPOS_EXCUSA = Object.entries(ETIQUETA_EXCUSA).map(([value, label]) => ({ value, label }))

function sinTildes(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export default function PaginaLlamadoLista() {
  const { evaluacionId = '' } = useParams()
  const [datos, setDatos] = useState<Seguimiento | null>(null)
  const [error, setError] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState<Filtro>('todos')
  const [marcando, setMarcando] = useState<number | null>(null)
  const [excusaPara, setExcusaPara] = useState<FilaSeguimiento | null>(null)
  const [tipoExcusa, setTipoExcusa] = useState<TipoExcusa | ''>('')
  const [observacion, setObservacion] = useState('')
  const [confirmarTodos, setConfirmarTodos] = useState(false)
  const [marcandoTodos, setMarcandoTodos] = useState(false)
  const { ahoraServidor, sincronizar } = useRelojServidor()

  const cargar = async () => {
    try {
      const r = await api.get<Seguimiento>(`/evaluacion/docente/supervision/${evaluacionId}/`)
      setDatos(r.data)
      sincronizar(r.data.ahora_servidor)
      setError('')
    } catch (err: unknown) {
      setError(mensajeError(err, 'No se encontró la evaluación o no eres su supervisor.'))
    }
  }
  useConsultaPeriodica(cargar)

  const marcar = async (fila: FilaSeguimiento, estado: EstadoAsistencia, extra?: { tipo_excusa: string; observacion: string }) => {
    setMarcando(fila.estudiante)
    try {
      await api.put(`/evaluacion/docente/supervision/${evaluacionId}/asistencia/`, {
        estudiante: fila.estudiante,
        estado,
        ...extra,
      })
      toast.success(`${fila.nombre}: ${ETIQUETA_ASISTENCIA[estado].toLowerCase()}`)
      await cargar()
      return true
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo registrar la asistencia'))
      return false
    } finally {
      setMarcando(null)
    }
  }

  const abrirExcusa = (fila: FilaSeguimiento) => {
    setExcusaPara(fila)
    setTipoExcusa(fila.asistencia?.tipo_excusa ?? '')
    setObservacion(fila.asistencia?.observacion ?? '')
  }

  const sinLlamar = useMemo(() => datos?.filas.filter((f) => !f.asistencia) ?? [], [datos])

  const marcarTodos = async () => {
    setMarcandoTodos(true)
    try {
      const r = await api.put<{ marcados: number }>(`/evaluacion/docente/supervision/${evaluacionId}/asistencia/masiva/`, {
        estudiantes: sinLlamar.map((f) => f.estudiante),
        estado: 'presente',
      })
      toast.success(`${r.data.marcados} estudiante(s) marcados presentes`)
      setConfirmarTodos(false)
      await cargar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo marcar a todos'))
    } finally {
      setMarcandoTodos(false)
    }
  }

  const visibles = useMemo(() => {
    if (!datos) return []
    const q = sinTildes(busqueda.trim())
    return datos.filas.filter((f) => {
      const estado = f.asistencia?.estado ?? 'sin_llamar'
      if (filtro === 'suspendido') {
        if (f.intento?.integridad?.estado !== 'suspendido') return false
      } else if (filtro !== 'todos' && estado !== filtro) return false
      return !q || sinTildes(`${f.nombre} ${f.email}`).includes(q)
    })
  }, [datos, busqueda, filtro])

  const volver = (
    <Link to="/supervision" className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Volver a mis supervisiones
    </Link>
  )

  if (!datos) {
    return (
      <div className="space-y-4">
        {volver}
        {error ? (
          <p role="alert" className="text-sm text-destructive">{error}</p>
        ) : (
          <div className="flex min-h-[40vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
          </div>
        )}
      </div>
    )
  }

  const ev = datos.evaluacion
  const enVentana =
    ahoraServidor >= new Date(ev.llamado_desde).getTime() && ahoraServidor <= new Date(ev.llamado_hasta).getTime()

  return (
    <div className="space-y-6">
      {volver}
      <div className="space-y-1">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-primary uppercase">
          {ev.programa} · {ev.momento}
        </p>
        <h1 className="font-heading text-2xl text-foreground sm:text-3xl">Llamado a lista · {ev.nombre}</h1>
        <p className="text-sm text-muted-foreground">
          {formatoFecha.format(new Date(ev.fecha_inicio))} → {formatoFecha.format(new Date(ev.fecha_fin))} ·{' '}
          {ev.duracion_minutos} min · {ev.total_preguntas} preguntas
        </p>
      </div>

      {!enVentana && (
        <p role="status" className="rounded-lg bg-warning/15 p-3 text-sm text-foreground">
          El llamado a lista se habilita desde {formatoFecha.format(new Date(ev.llamado_desde))} hasta el cierre.
        </p>
      )}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

      <TarjetasConteo conteos={datos.conteos} />

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por nombre o correo"
            aria-label="Buscar estudiante"
            className="pl-8"
          />
        </div>
        <Button onClick={() => setConfirmarTodos(true)} disabled={!enVentana || sinLlamar.length === 0}>
          <CheckCheck className="mr-1.5 h-4 w-4" aria-hidden />
          Marcar todos presentes ({sinLlamar.length})
        </Button>
      </div>

      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar por estado de asistencia">
        {FILTROS.map((f) => (
          <button
            key={f.valor}
            type="button"
            aria-pressed={filtro === f.valor}
            onClick={() => setFiltro(f.valor)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
              filtro === f.valor ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted',
            )}
          >
            {f.texto}
          </button>
        ))}
      </div>

      {visibles.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            {datos.filas.length === 0 ? 'No hay estudiantes convocados a esta evaluación.' : 'Ningún estudiante coincide con el filtro.'}
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {visibles.map((f) => {
            const actual = f.asistencia?.estado
            const ocupado = marcando === f.estudiante
            return (
              <li key={f.estudiante} className="rounded-xl border border-border bg-card p-3">
                <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_12rem] md:items-center">
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-foreground">{f.nombre}</span>
                      <ChipAsistencia estado={actual} />
                      <ChipIntegridad estado={f.intento?.integridad?.estado} />
                    </div>
                    <p className="text-xs break-all text-muted-foreground">{f.email}</p>
                    {(f.asistencia?.llegada_en || f.asistencia?.tipo_excusa || f.asistencia?.observacion) && (
                      <p className="text-xs text-muted-foreground">
                        {f.asistencia?.llegada_en && `Llegó ${formatoHora.format(new Date(f.asistencia.llegada_en))}`}
                        {f.asistencia?.tipo_excusa && ETIQUETA_EXCUSA[f.asistencia.tipo_excusa]}
                        {f.asistencia?.observacion && ` · ${f.asistencia.observacion}`}
                      </p>
                    )}
                  </div>
                  <div className="grid grid-cols-4 gap-1.5" role="group" aria-label={`Asistencia de ${f.nombre}`}>
                    {BOTONES.map((b) => {
                      // A quien ya inició no se le puede poner ausente ni excusa (el backend responde 409).
                      const bloqueado = !!f.intento && (b.estado === 'ausente' || b.estado === 'excusa')
                      return (
                        <Button
                          key={b.estado}
                          variant="outline"
                          size="sm"
                          aria-pressed={actual === b.estado}
                          disabled={!enVentana || ocupado || bloqueado}
                          className={cn('px-2', actual === b.estado && b.activo)}
                          onClick={() => (b.estado === 'excusa' ? abrirExcusa(f) : void marcar(f, b.estado))}
                        >
                          {ETIQUETA_ASISTENCIA[b.estado]}
                        </Button>
                      )
                    })}
                  </div>
                  <ProgresoIntento intento={f.intento} ahoraServidor={ahoraServidor} />
                </div>
                {f.intento?.integridad && (
                  <div className="mt-3">
                    <PanelIntegridad
                      integridad={f.intento.integridad}
                      nombre={f.nombre}
                      urlResolver={`/evaluacion/docente/supervision/${evaluacionId}/intentos/${f.estudiante}/resolver/`}
                      puedeResolver
                      alResolver={() => void cargar()}
                    />
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <Dialog open={!!excusaPara} onOpenChange={(v) => !v && setExcusaPara(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar excusa</DialogTitle>
            <DialogDescription>{excusaPara?.nombre} no presentará la evaluación en esta sesión.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="tipo-excusa">
                Tipo de excusa <span className="text-destructive" aria-hidden="true">*</span>
              </Label>
              <Select value={tipoExcusa || null} onValueChange={(v) => setTipoExcusa((v ?? '') as TipoExcusa | '')} items={TIPOS_EXCUSA}>
                <SelectTrigger id="tipo-excusa" className="w-full">
                  <SelectValue placeholder="Elige el tipo" />
                </SelectTrigger>
                <SelectContent>
                  {TIPOS_EXCUSA.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="obs-excusa">Observación</Label>
              <Textarea
                id="obs-excusa"
                maxLength={300}
                value={observacion}
                placeholder="Ej.: incapacidad médica de la EPS"
                onChange={(e) => setObservacion(e.target.value)}
              />
              <p className="text-right text-xs text-muted-foreground">{observacion.length}/300</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExcusaPara(null)}>
              Cancelar
            </Button>
            <Button
              disabled={!tipoExcusa || marcando !== null}
              onClick={async () => {
                if (excusaPara && (await marcar(excusaPara, 'excusa', { tipo_excusa: tipoExcusa, observacion }))) {
                  setExcusaPara(null)
                }
              }}
            >
              {marcando !== null && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Guardar excusa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmarTodos} onOpenChange={setConfirmarTodos}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>¿Marcar todos presentes?</DialogTitle>
            <DialogDescription>
              Se marcarán presentes los {sinLlamar.length} estudiante(s) que aún no se han llamado, y podrán iniciar la
              evaluación de inmediato. A los ya registrados no se les cambia nada.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmarTodos(false)} disabled={marcandoTodos}>
              Cancelar
            </Button>
            <Button onClick={() => void marcarTodos()} disabled={marcandoTodos}>
              {marcandoTodos && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Marcar presentes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
