// Notas del momento (ADR-019): resultado individual de cada estudiante en el momento
// (examen, trabajo, consolidado, nota reglamentaria y aportes al corte) y su Excel.
// Lo ven Administrador, Coordinador y Vicerrector; la ponderación examen/trabajo la
// define el gestor académico. Sin calificación ⇒ celda vacía con su estado (nunca 0).

import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { AlertTriangle, FileSpreadsheet, Info, Loader2, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FilaNotas, MomentoConNotas, NotasMomento } from '@/types/notas-momento'
import { mensajeError } from '@/pages/academico/academico-utils'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'
import {
  CLASE_NIVEL,
  FILTROS_ESTADO,
  type FiltrosMomento,
  coma,
  coincideFiltro,
  filtrarMomentos,
  rangoFechas,
} from './notas-momento-utils'

const BASE = '/evaluacion/notas-momento'

export default function PaginaNotasMomento() {
  const [params, setParams] = useSearchParams()
  const momentoId = params.get('momento') ?? ''
  const [momentos, setMomentos] = useState<MomentoConNotas[] | null>(null)
  const [datos, setDatos] = useState<NotasMomento | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState('todos')
  const [exportando, setExportando] = useState(false)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    api.get<MomentoConNotas[]>(`${BASE}/momentos/`).then((r) => setMomentos(r.data)).catch(() => setMomentos([]))
  }, [])

  useEffect(() => {
    if (!momentoId) return
    let vigente = true
    api
      .get<NotasMomento>(`${BASE}/${momentoId}/`)
      .then((r) => vigente && setDatos(r.data))
      .catch((err: unknown) => vigente && toast.error(mensajeError(err, 'No se pudieron cargar las notas')))
    return () => {
      vigente = false
    }
  }, [momentoId, version])

  // Actualizaciones funcionales: cada cambio parte de la URL vigente, no de la del último render.
  const elegir = (id: string) => {
    setParams((actual) => {
      const nuevos = new URLSearchParams(actual)
      nuevos.set('momento', id)
      return nuevos
    }, { replace: true })
  }

  const cargando = !!momentoId && (!datos || String(datos.momento.id) !== momentoId)
  const filas = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return (datos?.filas ?? []).filter(
      (f) => coincideFiltro(f, filtro) && (!q || `${f.nombre} ${f.correo} ${f.codigo}`.toLowerCase().includes(q)),
    )
  }, [datos, busqueda, filtro])

  const exportar = async () => {
    if (!datos) return
    setExportando(true)
    try {
      await descargarArchivo(`${BASE}/${datos.momento.id}/exportar/`, `notas_momento_${datos.momento.id}.xlsx`)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo exportar'))
    } finally {
      setExportando(false)
    }
  }

  // Filtros del selector (pedido del dueño del proyecto): viven en la URL para poder
  // recargar o compartir la vista con los mismos filtros.
  const filtros: FiltrosMomento = {
    q: params.get('q') ?? '',
    programa: params.get('programa') ?? '',
    periodo: params.get('periodo') ?? '',
    desde: params.get('desde') ?? '',
    hasta: params.get('hasta') ?? '',
  }
  const hayFiltros = Object.values(filtros).some(Boolean)
  const cambiarFiltro = (clave: keyof FiltrosMomento, valor: string) => {
    setParams((actual) => {
      const nuevos = new URLSearchParams(actual)
      if (valor) nuevos.set(clave, valor)
      else nuevos.delete(clave)
      return nuevos
    }, { replace: true })
  }
  const limpiarFiltros = () => {
    setParams((actual) => {
      const nuevos = new URLSearchParams()
      const momento = actual.get('momento')
      if (momento) nuevos.set('momento', momento)
      return nuevos
    }, { replace: true })
  }

  const programas = useMemo(() => {
    const unicos = new Map<number, string>()
    for (const m of momentos ?? []) unicos.set(m.programa_id, m.programa)
    return [...unicos].map(([id, nombre]) => ({ value: String(id), label: nombre }))
  }, [momentos])
  const periodos = useMemo(
    () => [...new Set((momentos ?? []).map((m) => m.periodo).filter(Boolean))].sort().reverse(),
    [momentos],
  )
  const { q, programa, periodo, desde, hasta } = filtros
  const filtrados = useMemo(
    () => filtrarMomentos(momentos ?? [], { q, programa, periodo, desde, hasta }),
    [momentos, q, programa, periodo, desde, hasta],
  )

  const items = filtrados.map((m) => {
    const rango = rangoFechas(m)
    return {
      value: String(m.id),
      label: `${m.programa} · ${m.nombre}${m.periodo ? ` (${m.periodo})` : ''}${rango ? ` · ${rango}` : ''}`,
    }
  })
  const opcionesPrograma = [{ value: '', label: 'Todos los programas' }, ...programas]
  const opcionesPeriodo = [{ value: '', label: 'Todos los periodos' }, ...periodos.map((p) => ({ value: p, label: p }))]

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Resultados de aprendizaje"
        titulo="Notas del momento"
        subtitulo="Resultado individual de cada estudiante: examen, trabajo, consolidado del momento y su aporte al tercer corte. Escala y redondeo institucionales."
        accion={
          datos && (
            <Button onClick={exportar} disabled={exportando}>
              {exportando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <FileSpreadsheet className="mr-1.5 h-4 w-4" aria-hidden />}
              Exportar Excel
            </Button>
          )
        }
      />

      <Card>
        <CardContent className="space-y-4 p-4">
          {momentos === null ? (
            <Loader2 className="h-5 w-5 animate-spin text-primary" aria-label="Cargando momentos" />
          ) : momentos.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aún no hay momentos con evaluaciones publicadas.</p>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[minmax(0,2fr)_minmax(0,1.5fr)_minmax(0,1fr)_auto_auto] lg:items-end">
                <div className="min-w-0 space-y-1">
                  <Label htmlFor="buscar-momento">Buscar</Label>
                  <div className="relative">
                    <Search className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                    <Input
                      id="buscar-momento"
                      value={filtros.q}
                      onChange={(e) => cambiarFiltro('q', e.target.value)}
                      placeholder="Momento, programa o periodo"
                      className="pl-8"
                    />
                  </div>
                </div>
                <div className="min-w-0 space-y-1">
                  <Label htmlFor="filtro-programa">Programa</Label>
                  <Select value={filtros.programa} onValueChange={(v) => cambiarFiltro('programa', String(v ?? ''))} items={opcionesPrograma}>
                    <SelectTrigger id="filtro-programa" className="w-full min-w-0">
                      <SelectValue placeholder="Todos los programas" />
                    </SelectTrigger>
                    <SelectContent>
                      {opcionesPrograma.map((o) => (
                        <SelectItem key={o.value || 'todos'} value={o.value}>
                          {o.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="min-w-0 space-y-1">
                  <Label htmlFor="filtro-periodo">Periodo</Label>
                  <Select value={filtros.periodo} onValueChange={(v) => cambiarFiltro('periodo', String(v ?? ''))} items={opcionesPeriodo}>
                    <SelectTrigger id="filtro-periodo" className="w-full min-w-0">
                      <SelectValue placeholder="Todos los periodos" />
                    </SelectTrigger>
                    <SelectContent>
                      {opcionesPeriodo.map((o) => (
                        <SelectItem key={o.value || 'todos'} value={o.value}>
                          {o.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="filtro-desde">Desde</Label>
                  <Input id="filtro-desde" type="date" value={filtros.desde} max={filtros.hasta || undefined}
                    onChange={(e) => cambiarFiltro('desde', e.target.value)} />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="filtro-hasta">Hasta</Label>
                  <Input id="filtro-hasta" type="date" value={filtros.hasta} min={filtros.desde || undefined}
                    onChange={(e) => cambiarFiltro('hasta', e.target.value)} />
                </div>
              </div>

              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <Label htmlFor="notas-momento">Momento</Label>
                  <span className="text-xs text-muted-foreground" aria-live="polite">
                    {filtrados.length} de {momentos.length} momento(s)
                    {hayFiltros && (
                      <>
                        {' · '}
                        <button type="button" onClick={limpiarFiltros} className="font-medium text-primary hover:underline">
                          Limpiar filtros
                        </button>
                      </>
                    )}
                  </span>
                </div>
                {filtrados.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Ningún momento coincide con los filtros.</p>
                ) : (
                  <Select value={momentoId} onValueChange={(v) => v && elegir(String(v))} items={items}>
                    <SelectTrigger id="notas-momento" className="w-full min-w-0">
                      <SelectValue placeholder="Elige un momento" />
                    </SelectTrigger>
                    <SelectContent>
                      {items.map((i) => (
                        <SelectItem key={i.value} value={i.value}>
                          {i.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {!momentoId && momentos && momentos.length > 0 && (
        <p className="text-sm text-muted-foreground">Elige un momento para ver las notas de sus estudiantes.</p>
      )}
      {cargando && (
        <div className="flex justify-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
        </div>
      )}

      {datos && !cargando && (
        <>
          {datos.provisional && (
            <p role="status" className="flex items-start gap-2 rounded-xl border border-warning/50 bg-warning/5 p-3 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
              Resultados provisionales: hay evaluaciones abiertas, intentos en curso o suspendidos, trabajos sin calificar o la ponderación examen/trabajo sin definir.
            </p>
          )}

          <Esquema key={`${datos.momento.id}-${datos.esquema.peso_examen}`} datos={datos} alGuardar={() => setVersion((v) => v + 1)} />
          <Indicadores datos={datos} />

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Resultados individuales</CardTitle>
              <CardDescription>
                {datos.filas.length} estudiante(s) convocado(s). Las celdas sin nota no son cero: el estado explica el motivo.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <div className="relative min-w-0 flex-1">
                  <Search className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                  <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Nombre, correo o código"
                    aria-label="Buscar estudiante" className="pl-8" />
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar por estado">
                {FILTROS_ESTADO.map((f) => (
                  <button key={f.clave} type="button" onClick={() => setFiltro(f.clave)} aria-pressed={filtro === f.clave}
                    className={cn('rounded-full border px-3 py-1 text-xs transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                      filtro === f.clave ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground hover:bg-muted')}>
                    {f.etiqueta}
                  </button>
                ))}
              </div>
              <div className="overflow-x-auto rounded-xl border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[13rem]">Estudiante</TableHead>
                      <TableHead className="text-right">Examen</TableHead>
                      <TableHead className="min-w-[9rem]">Preguntas</TableHead>
                      {datos.tiene_trabajo && <TableHead className="text-right">Trabajo</TableHead>}
                      <TableHead className="text-right">Momento</TableHead>
                      <TableHead className="text-right" title="Aplica 0,0 solo a lo no presentado sin excusa (Acuerdo 005 de 2025)">Reglamentaria</TableHead>
                      <TableHead className="text-right">Aporte corte / definitiva</TableHead>
                      <TableHead className="min-w-[12rem]">Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filas.map((f) => <FilaEstudiante key={f.estudiante_id} f={f} conTrabajo={datos.tiene_trabajo} etiquetas={datos.resumen.etiquetas_nivel} />)}
                  </TableBody>
                </Table>
                {!filas.length && <p className="p-4 text-sm text-muted-foreground">Ningún estudiante coincide con la búsqueda o el filtro.</p>}
              </div>
            </CardContent>
          </Card>

          <p className="flex items-start gap-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            Los aportes no son la nota del tercer corte: las demás actividades del corte las define el profesor y se registran en el sistema académico. Fuentes: {datos.fuentes.escala_redondeo}; niveles y peso del momento: {datos.fuentes.niveles}.
          </p>
        </>
      )}
    </div>
  )
}

function Nota({ valor, nivel, etiquetas }: { valor: number | null; nivel: FilaNotas['examen']['nivel']; etiquetas: Record<string, string> }) {
  if (valor === null) return <span className="text-muted-foreground" aria-label="Sin calificación">—</span>
  return (
    <span className="inline-flex flex-col items-end">
      <span className="font-semibold text-foreground tabular-nums">{coma(valor)}</span>
      {nivel && <Badge variant="outline" className={cn('mt-0.5 font-normal', CLASE_NIVEL[nivel])}>{etiquetas[nivel]}</Badge>}
    </span>
  )
}

function FilaEstudiante({ f, conTrabajo, etiquetas }: { f: FilaNotas; conTrabajo: boolean; etiquetas: Record<string, string> }) {
  const ex = f.examen
  return (
    <TableRow>
      <TableCell>
        <span className="font-medium text-foreground">{f.nombre}</span>
        <span className="block text-xs text-muted-foreground">{f.codigo ? `${f.codigo} · ` : ''}{f.correo}</span>
      </TableCell>
      <TableCell className="text-right"><Nota valor={ex.nota} nivel={ex.nivel} etiquetas={etiquetas} /></TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {ex.total !== null ? (
          <>
            <span className="text-foreground">{ex.correctas} correctas</span> · {ex.incorrectas} incorrectas
            {ex.sin_responder ? ` · ${ex.sin_responder} sin responder` : ''}
            <span className="block">{ex.total} preguntas · {coma(ex.porcentaje)} %</span>
          </>
        ) : '—'}
      </TableCell>
      {conTrabajo && <TableCell className="text-right"><Nota valor={f.trabajo.nota} nivel={f.trabajo.nivel} etiquetas={etiquetas} /></TableCell>}
      <TableCell className="text-right"><Nota valor={f.momento.nota} nivel={f.momento.nivel} etiquetas={etiquetas} /></TableCell>
      <TableCell className="text-right tabular-nums">{f.momento.nota_reglamentaria === null ? <span className="text-muted-foreground">—</span> : coma(f.momento.nota_reglamentaria)}</TableCell>
      <TableCell className="text-right text-xs tabular-nums">
        {f.momento.aporte_tercer_corte === null ? <span className="text-muted-foreground">—</span> : (
          <>{coma(f.momento.aporte_tercer_corte, 2)} <span className="text-muted-foreground">/ {coma(f.momento.aporte_definitiva, 2)}</span></>
        )}
      </TableCell>
      <TableCell className="text-xs">
        <span className="block text-foreground">{ex.estado_texto}</span>
        {conTrabajo && <span className="block text-muted-foreground">Trabajo: {f.trabajo.estado_texto}</span>}
        {f.momento.estado !== 'calificado' && <span className="block text-warning">{f.momento.estado_texto}</span>}
      </TableCell>
    </TableRow>
  )
}

function Indicadores({ datos }: { datos: NotasMomento }) {
  const r = datos.resumen
  const tarjetas = [
    { t: 'Convocados', v: String(r.convocados), d: `${r.examen.presentaron} presentaron (${coma(r.examen.pct_presentaron)} %)` },
    { t: 'Ausentes o no presentaron', v: String(r.examen.ausentes), d: `${coma(r.examen.pct_ausentes)} % · ${r.examen.con_excusa} con excusa · ${r.examen.anulados} anulado(s)` },
    { t: 'Promedio del momento', v: coma(r.momento.promedio), d: `Meta ≥ ${coma(r.momento.meta_promedio)} · ${r.momento.con_nota} con nota`, ok: r.momento.cumple_promedio },
    { t: 'Aprobación (≥ 3,0)', v: r.momento.pct_aprobacion === null ? '—' : `${coma(r.momento.pct_aprobacion)} %`, d: `Meta ≥ ${coma(r.momento.meta_aprobacion)} % · ${r.momento.aprobados} aprobado(s)`, ok: r.momento.cumple_aprobacion },
  ]
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {tarjetas.map((x) => (
          <Card key={x.t}>
            <CardContent className="p-4">
              <p className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{x.t}</p>
              <p className={cn('text-2xl font-semibold tabular-nums', x.ok === false && 'text-destructive', x.ok === true && 'text-success')}>{x.v}</p>
              <p className="text-xs text-muted-foreground">{x.d}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardContent className="flex flex-wrap items-center gap-2 p-4 text-sm">
          <span className="text-muted-foreground">Desempeño del momento:</span>
          {r.momento.niveles.map((n) => (
            <Badge key={n.clave} variant="outline" className={cn('font-normal', CLASE_NIVEL[n.clave])}>
              {n.etiqueta}: {n.cantidad}{n.porcentaje !== null ? ` (${coma(n.porcentaje)} %)` : ''}
            </Badge>
          ))}
          <span className="text-xs text-muted-foreground">Promedios e indicadores solo con quienes tienen nota.</span>
        </CardContent>
      </Card>
    </div>
  )
}

function Esquema({ datos, alGuardar }: { datos: NotasMomento; alGuardar: () => void }) {
  const e = datos.esquema
  const [examen, setExamen] = useState(e.peso_examen === null ? '' : String(e.peso_examen))
  const [guardando, setGuardando] = useState(false)
  const trabajo = examen === '' ? '' : String(Math.max(0, 100 - Number(examen)))

  const guardar = async () => {
    setGuardando(true)
    try {
      await api.put(`${BASE}/${datos.momento.id}/esquema/`, examen === ''
        ? { peso_examen: null, peso_trabajo: null }
        : { peso_examen: Number(examen), peso_trabajo: Number(trabajo) })
      toast.success('Ponderación guardada')
      alGuardar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la ponderación'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Cómo se calcula</CardTitle>
        <CardDescription>
          Examen: 5 × correctas / total de preguntas de todos los cuestionarios del momento. Un decimal, redondeo reglamentario.
          El momento vale {coma(e.peso_momento_en_corte)} % del tercer corte y el tercer corte {coma(e.peso_corte_en_definitiva)} % de la nota definitiva.
        </CardDescription>
      </CardHeader>
      {datos.tiene_trabajo && (
        <CardContent className="space-y-2">
          {e.ponderacion_definida ? (
            <p className="text-sm">
              Consolidado = <strong>{coma(e.peso_examen)} % examen</strong> + <strong>{coma(e.peso_trabajo)} % trabajo</strong>
              <span className="text-muted-foreground"> ({e.origen_peso_examen === 'momento' ? 'definido para este momento' : 'valor institucional'})</span>
            </p>
          ) : (
            <p className="flex items-start gap-2 text-sm text-warning">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              Este momento tiene trabajo, pero la ponderación examen/trabajo no está definida: el consolidado queda pendiente.
            </p>
          )}
          {datos.puede_editar_esquema && (
            <div className="flex flex-wrap items-end gap-2">
              <div className="space-y-1">
                <Label htmlFor="peso-examen">% del examen</Label>
                <Input id="peso-examen" type="number" min={0} max={100} value={examen} onChange={(ev) => setExamen(ev.target.value)} className="w-28" />
              </div>
              <div className="space-y-1">
                <Label htmlFor="peso-trabajo">% del trabajo</Label>
                <Input id="peso-trabajo" value={trabajo} readOnly className="w-28 bg-muted" />
              </div>
              <Button variant="outline" onClick={guardar} disabled={guardando || (examen !== '' && (Number(examen) < 0 || Number(examen) > 100))}>
                {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                Guardar ponderación
              </Button>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
