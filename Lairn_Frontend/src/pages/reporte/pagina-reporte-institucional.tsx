// Reporte institucional de resultados de aprendizaje (HU-11 + ADR-011 + ADR-015).
// Solo lectura para Vicerrectoría, Coordinación y Administración.
//
// Recorrido guiado en 6 etapas, para no leer decenas de gráficos a la vez:
//   1. Panorama        ¿cuál es la situación actual?
//   2. Hallazgos       ¿qué requiere atención y qué va bien? (con evidencia)
//   3. Profundizar     ¿dónde ocurre? (RA, competencias, mapas, preguntas, cursos)
//   4. Comparar        ¿qué cambió y cómo se comparan programas, semestres y momentos?
//   5. Conclusiones    síntesis descriptiva y limitaciones
//   6. Evidencia       tablas, fichas técnicas, calidad de datos y exportación
// Los filtros (en la URL) y la etapa (?etapa=) se conservan al navegar.
// Cada cifra abre su ficha técnica. La métrica de logro es PROVISIONAL (ADR-006)
// y todos los indicadores son institucionales propios, no oficiales del MEN.

import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { ArrowLeft, ArrowRight, ChevronRight, FileSpreadsheet, FileText, Info, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { mensajeError } from '@/pages/academico/academico-utils'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'
import type { FichaIndicador, FiltroReporte, Hallazgo, OpcionesReporte, Reporte } from '@/types/reporte'
import { FiltrosReporte } from './componentes/filtros-reporte'
import { LeyendaCalor, MapaCalor } from './componentes/mapa-calor'
import { BarrasLogro, GraficoTendencia, NivelesDesempeno, RadarCompetencias, TarjetaKpi } from './componentes/graficos-reporte'
import { BotonFicha, DialogoFicha, EtapasNav, Seccion, TarjetaHallazgo } from './componentes/recorrido'
import { ETAPAS, NIVEL_INDICADOR, aParams, combinar, irANivel, leerFiltros, pct, tonoLogro, type ClaveEtapa } from './reporte-utils'

const configNotas: ChartConfig = { cantidad: { label: 'Resultados', color: 'var(--primary)' } }
const formatoCorte = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
const FUENTE_OBS = 'intentos enviados (no anulados) de evaluaciones formales tipo cuestionario · LAIRN'

type ClaveMapa = 'ra_asignatura' | 'competencia_programa' | 'ra_momento'
const MAPAS: { clave: ClaveMapa; titulo: string; filas: string }[] = [
  { clave: 'ra_asignatura', titulo: 'RA × asignatura', filas: 'Resultado de aprendizaje' },
  { clave: 'competencia_programa', titulo: 'Competencia × programa', filas: 'Competencia' },
  { clave: 'ra_momento', titulo: 'RA × momento', filas: 'Resultado de aprendizaje' },
]
const GRUPOS_HALLAZGO: { tipo: Hallazgo['tipo']; titulo: string }[] = [
  { tipo: 'atencion', titulo: 'Requieren atención' },
  { tipo: 'positivo', titulo: 'Resultados favorables' },
  { tipo: 'informativo', titulo: 'Para tener en cuenta' },
  { tipo: 'calidad', titulo: 'Calidad y suficiencia de los datos' },
]

function Provisional() {
  return <Badge variant="outline" className="shrink-0 border-warning/60 font-normal text-foreground">Provisional</Badge>
}

function Datos({ items }: { items: [string, string | number][] }) {
  return (
    <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
      {items.map(([t, v]) => (
        <div key={t} className="rounded-lg bg-muted/40 p-3">
          <dt className="text-xs text-muted-foreground">{t}</dt>
          <dd className="text-lg font-semibold tabular-nums text-foreground">{v}</dd>
        </div>
      ))}
    </dl>
  )
}

export default function PaginaReporteInstitucional() {
  const [params, setParams] = useSearchParams()
  const etapa = (ETAPAS.some((e) => e.clave === params.get('etapa')) ? params.get('etapa') : 'panorama') as ClaveEtapa
  // La clave de datos excluye la etapa: cambiar de etapa no vuelve a consultar.
  const filtrosParams = new URLSearchParams(params)
  filtrosParams.delete('etapa')
  const clave = filtrosParams.toString()
  const filtros = leerFiltros(filtrosParams)
  const [datos, setDatos] = useState<Reporte | null>(null)
  const [opciones, setOpciones] = useState<OpcionesReporte | null>(null)
  const [fichas, setFichas] = useState<FichaIndicador[]>([])
  const [ficha, setFicha] = useState<FichaIndicador | null>(null)
  const [error, setError] = useState('')
  const [claveCargada, setClaveCargada] = useState<string | null>(null)
  const cargando = claveCargada !== clave
  const [exportando, setExportando] = useState<'pdf' | 'xlsx' | null>(null)
  const [mapa, setMapa] = useState<ClaveMapa>('ra_asignatura')

  useEffect(() => {
    let activo = true
    api
      .get<Reporte>(`/evaluacion/reporte-ejecutivo/${clave ? `?${clave}` : ''}`)
      .then((res) => {
        if (activo) {
          setDatos(res.data)
          setError('')
        }
      })
      .catch((err: unknown) => activo && setError(mensajeError(err, 'No se pudo cargar el reporte.')))
      .finally(() => activo && setClaveCargada(clave))
    return () => {
      activo = false
    }
  }, [clave])

  useEffect(() => {
    api
      .get<{ indicadores: FichaIndicador[] }>('/evaluacion/reporte-ejecutivo/indicadores/')
      .then((r) => setFichas(r.data.indicadores))
      .catch(() => setFichas([]))
  }, [])
  const fichaDe = useMemo(() => Object.fromEntries(fichas.map((f) => [f.id, f])), [fichas])
  const conFicha = (id: string) => <BotonFicha ficha={fichaDe[id]} alAbrir={setFicha} />

  const programa = filtrosParams.get('programa') ?? ''
  const semestre = filtrosParams.get('semestre') ?? ''
  useEffect(() => {
    const q = new URLSearchParams(aParams({ programa, semestre })).toString()
    api
      .get<OpcionesReporte>(`/evaluacion/reporte-ejecutivo/opciones/${q ? `?${q}` : ''}`)
      .then((res) => setOpciones(res.data))
      .catch(() => setOpciones(null))
  }, [programa, semestre])

  const ir = (nuevos: FiltroReporte, nuevaEtapa: ClaveEtapa = etapa) => {
    const p = aParams(nuevos)
    if (nuevaEtapa !== 'panorama') p.etapa = nuevaEtapa
    setParams(p)
  }
  const aplicar = (nuevos: FiltroReporte) => ir(nuevos)
  const abrir = (filtro: FiltroReporte, destino: ClaveEtapa = 'profundizar') => ir(combinar(filtros, filtro), destino)
  const irEtapa = (e: ClaveEtapa) => {
    ir(filtros, e)
    window.scrollTo({ top: 0 })
  }

  const exportar = async (formato: 'pdf' | 'xlsx') => {
    setExportando(formato)
    try {
      const q = new URLSearchParams({ ...aParams(filtros), formato }).toString()
      await descargarArchivo(`/evaluacion/reporte-ejecutivo/exportar/?${q}`, `reporte_institucional.${formato}`)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo generar el archivo'))
    } finally {
      setExportando(null)
    }
  }

  const a = datos?.analitica
  const ind = datos?.indicadores
  const umbral = a?.metrica_provisional.umbral_logro_porcentaje ?? 60
  const esInstitucion = datos?.nivel !== 'programa'
  const indice = ETAPAS.findIndex((e) => e.clave === etapa)
  const actual = ETAPAS[indice]
  const periodo = filtros.desde || filtros.hasta ? `${filtros.desde ?? 'inicio'} a ${filtros.hasta ?? 'hoy'}` : 'Todo el historial disponible'

  const botonesExportar = (
    <div className="flex flex-col gap-2 sm:flex-row">
      <Button variant="outline" onClick={() => void exportar('pdf')} disabled={!datos || exportando !== null}>
        {exportando === 'pdf' ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <FileText className="mr-1.5 h-4 w-4" aria-hidden />}
        Exportar PDF
      </Button>
      <Button variant="outline" onClick={() => void exportar('xlsx')} disabled={!datos || exportando !== null}>
        {exportando === 'xlsx' ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <FileSpreadsheet className="mr-1.5 h-4 w-4" aria-hidden />}
        Exportar Excel
      </Button>
    </div>
  )

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        eyebrow="Analítica institucional · resultados de aprendizaje"
        titulo="Informe de resultados de aprendizaje"
        subtitulo="Un recorrido en seis pasos: de la situación general a la evidencia que la respalda."
        accion={botonesExportar}
      />

      <FiltrosReporte filtros={filtros} opciones={opciones} alCambiar={aplicar} />

      {a && (
        <nav aria-label="Nivel del reporte" className="flex flex-wrap items-center gap-1 text-sm">
          {a.ruta.map((r, i) => {
            const ultimo = i === a.ruta.length - 1
            return (
              <span key={r.nivel} className="flex items-center gap-1">
                {i > 0 && <ChevronRight className="h-4 w-4 text-muted-foreground" aria-hidden />}
                <button
                  type="button"
                  onClick={() => aplicar(irANivel(filtros, r.filtros))}
                  aria-current={ultimo ? 'page' : undefined}
                  className={cn('max-w-64 truncate', ultimo ? 'font-medium text-foreground' : 'text-primary hover:underline')}
                >
                  {r.nombre}
                </button>
              </span>
            )
          })}
          <span className="ml-auto text-xs text-muted-foreground">
            {periodo} · corte {a ? formatoCorte.format(new Date(a.fecha_corte)) : ''}
          </span>
          {cargando && <Loader2 className="h-4 w-4 animate-spin text-primary" aria-label="Actualizando" />}
        </nav>
      )}

      <EtapasNav actual={etapa} alElegir={irEtapa} />

      {!datos && cargando ? (
        <div className="flex min-h-[40vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando reporte" />
        </div>
      ) : error && !datos ? (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      ) : a && ind && datos ? (
        <div className={cn('space-y-6 transition-opacity', cargando && 'opacity-60')}>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <header className="space-y-1">
            <p className="text-[11px] font-semibold tracking-[0.14em] text-primary uppercase">Paso {indice + 1} de {ETAPAS.length}</p>
            <h2 className="font-heading text-2xl text-foreground">{actual.pregunta}</h2>
            <p className="max-w-3xl text-sm text-muted-foreground">{actual.ayuda}</p>
          </header>

          {/* ───────────── 1. Panorama ───────────── */}
          {etapa === 'panorama' && (
            <>
              <p role="note" className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm text-foreground">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
                <span>
                  {a.metrica_provisional.aviso} Indicadores institucionales propios (no son indicadores oficiales del MEN). Pulsa{' '}
                  <Info className="inline h-3.5 w-3.5" aria-hidden /> en cada cifra para ver cómo se calcula.
                </span>
              </p>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <TarjetaKpi titulo="Logro general" valor={pct(a.logro_general.porcentaje)} tono={tonoLogro(a.logro_general.porcentaje, umbral).texto} detalle={`n = ${a.logro_general.presentadas} respuestas · umbral ${umbral} %`} accion={conFicha('logro_general')} />
                <TarjetaKpi titulo="RA logrados" valor={`${a.logro_general.ra_logrados} / ${a.logro_general.ra_evaluados}`} detalle="RA evaluados que alcanzan el umbral" accion={conFicha('ra_logrados')} />
                <TarjetaKpi titulo="% aprobación" valor={pct(a.niveles.aprobacion)} detalle={`${a.niveles.total} nota(s) en nivel Suficiente o superior`} accion={conFicha('aprobacion')} />
                <TarjetaKpi titulo="Cobertura de RA" valor={(() => { const o = a.cobertura.reduce((s, c) => s + c.obligatorios, 0); const e = a.cobertura.reduce((s, c) => s + c.evaluados, 0); return o ? `${e} / ${o}` : '—' })()} detalle="RA obligatorios con evaluación publicada" accion={conFicha('cobertura_ra')} />
                <TarjetaKpi titulo="Participación" valor={pct(a.participacion.porcentaje_participacion)} detalle={`${a.participacion.presentaron} de ${a.participacion.convocados} convocatorias`} accion={conFicha('participacion')} />
                <TarjetaKpi titulo="Estudiantes evaluados" valor={String(ind.estudiantes)} detalle={`de ${a.contexto.estudiantes} activos`} accion={conFicha('notas')} />
                <TarjetaKpi titulo="Alertas abiertas" valor={String(a.alertas.abiertas)} tono={a.alertas.abiertas ? 'text-warning' : undefined} detalle="alerta temprana" accion={conFicha('alertas')} />
                <TarjetaKpi titulo="Integridad" valor={`${a.integridad.suspensiones} / ${a.integridad.anulaciones}`} tono={a.integridad.anulaciones ? 'text-destructive' : undefined} detalle="suspensiones / anulaciones" accion={conFicha('integridad')} />
              </div>
              <Seccion titulo="En resumen" descripcion="Lo esencial antes de entrar en detalle.">
                <ul className="list-disc space-y-1 pl-5 text-sm text-foreground">
                  {a.conclusiones.puntos.slice(0, 3).map((p) => <li key={p}>{p}</li>)}
                </ul>
                {a.hallazgos.filter((h) => h.tipo === 'atencion').length > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Hay <strong className="text-foreground">{a.hallazgos.filter((h) => h.tipo === 'atencion').length} situación(es)</strong> que requieren atención: revísalas en el paso 2.
                  </p>
                )}
              </Seccion>
              <Seccion titulo="Contexto institucional" descripcion="Totales de la plataforma (o del programa filtrado)." fuente="usuarios, ev_programas, ev_asignaturas, cursos · LAIRN">
                <Datos items={[['Programas activos', a.contexto.programas], ['Estudiantes', a.contexto.estudiantes], ['Docentes', a.contexto.docentes], ['Coordinadores', a.contexto.coordinadores], ['Asignaturas', a.contexto.asignaturas], ['Cursos', a.contexto.cursos]]} />
              </Seccion>
            </>
          )}

          {/* ───────────── 2. Hallazgos ───────────── */}
          {etapa === 'hallazgos' && (
            <>
              {GRUPOS_HALLAZGO.map((g) => {
                const lista = a.hallazgos.filter((h) => h.tipo === g.tipo)
                if (lista.length === 0) return null
                return (
                  <section key={g.tipo} aria-label={g.titulo} className="space-y-2">
                    <h3 className="text-sm font-semibold text-foreground">{g.titulo} ({lista.length})</h3>
                    <ul className="grid gap-3 lg:grid-cols-2">
                      {lista.map((h, i) => (
                        <TarjetaHallazgo key={i} hallazgo={h} alAbrir={h.filtro ? () => abrir(h.filtro!, h.etapa) : h.etapa !== 'hallazgos' ? () => irEtapa(h.etapa) : undefined} />
                      ))}
                    </ul>
                  </section>
                )
              })}
              <p className="text-xs text-muted-foreground">
                Los hallazgos se generan con reglas explícitas sobre las cifras filtradas (umbral {umbral} %, variaciones ≥ 10 pp, participación &lt; 80 %, error ≥ 70 %, muestra &lt; 30). Describen; no explican causas.
              </p>
            </>
          )}

          {/* ───────────── 3. Profundizar ───────────── */}
          {etapa === 'profundizar' && (
            <>
              <Seccion titulo={`Detalle por ${a.desglose.titulo.toLowerCase()}`} descripcion={a.desglose.nivel ? 'Elige una fila para bajar un nivel (institución → programa → semestre → asignatura → RA → evaluación).' : 'Último nivel del recorrido.'} fuente={FUENTE_OBS} accion={<Provisional />}>
                <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.desglose.filas.map((f) => ({ ...f, titulo: f.nombre }))} />
              </Seccion>
              <div className="grid gap-6 lg:grid-cols-2">
                <Seccion titulo="Logro por resultado de aprendizaje" descripcion="% de acierto · los más débiles primero." fuente={FUENTE_OBS} accion={conFicha('logro_ra')}>
                  <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.logro_ra.map((r) => ({ ...r, titulo: r.descripcion, etiqueta: r.asignatura, subtitulo: `${r.competencia} · ${r.programa}` }))} />
                </Seccion>
                <Seccion titulo="Logro por competencia" descripcion="% de acierto · específicas y transversales." fuente={FUENTE_OBS} accion={conFicha('logro_competencia')}>
                  {a.logro_competencia.length >= 3 && <RadarCompetencias competencias={a.logro_competencia} />}
                  <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.logro_competencia.map((c) => ({ ...c, titulo: c.nombre, subtitulo: `${c.tipo === 'transversal' ? 'Transversal' : 'Específica'} · ${c.programa}` }))} />
                </Seccion>
              </div>
              <Seccion titulo="Mapa de calor" descripcion="% de logro por cruce; cada celda muestra n y abre su detalle. Celda vacía = sin datos (no es 0)." fuente={FUENTE_OBS} accion={<Provisional />}>
                <div role="tablist" aria-label="Tipo de mapa de calor" className="flex flex-wrap gap-1.5">
                  {MAPAS.map((m) => (
                    <button key={m.clave} type="button" role="tab" aria-selected={mapa === m.clave} onClick={() => setMapa(m.clave)}
                      className={cn('rounded-full border px-3 py-1 text-xs focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none', mapa === m.clave ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted')}>
                      {m.titulo}
                    </button>
                  ))}
                </div>
                <LeyendaCalor umbral={umbral} />
                <MapaCalor mapa={a.mapas[mapa]} umbral={umbral} etiquetaFilas={MAPAS.find((m) => m.clave === mapa)!.filas} alAbrir={(f) => abrir(f)} />
              </Seccion>
              <div className="grid gap-6 lg:grid-cols-2">
                <Seccion titulo="Preguntas con mayor % de error" descripcion="Para revisar redacción, dificultad o enseñanza." fuente={FUENTE_OBS} accion={conFicha('preguntas_error')}>
                  {a.mapas.preguntas_error.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Sin datos con los filtros aplicados.</p>
                  ) : (
                    <ol className="space-y-2">
                      {a.mapas.preguntas_error.map((q) => {
                        const tono = tonoLogro(q.porcentaje_error === null ? null : 100 - q.porcentaje_error, umbral)
                        return (
                          <li key={q.pregunta}>
                            <button type="button" onClick={() => abrir(q.filtro)} className="w-full rounded-lg border border-border p-2.5 text-left hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                              <span className="flex items-start justify-between gap-2">
                                <span className="line-clamp-2 text-sm text-foreground">{q.enunciado}</span>
                                <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-semibold', tono.fondo, tono.texto)}>{pct(q.porcentaje_error)} error</span>
                              </span>
                              <span className="mt-1 block text-xs text-muted-foreground">{q.asignatura} · n={q.presentadas}</span>
                            </button>
                          </li>
                        )
                      })}
                    </ol>
                  )}
                </Seccion>
                <Seccion titulo="Participación por curso" descripcion="Convocados (inscritos) que presentaron · menor primero." fuente="inscripciones, ev_intentos_evaluacion, ev_entregas_tarea · LAIRN" accion={conFicha('participacion')}>
                  {a.mapas.participacion_curso.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Sin evaluaciones publicadas con cursos vinculados.</p>
                  ) : (
                    <ul className="space-y-3">
                      {a.mapas.participacion_curso.map((c) => (
                        <li key={c.curso}>
                          <div className="flex justify-between gap-2 text-sm">
                            <span className="min-w-0 truncate text-foreground">{c.nombre}</span>
                            <span className="shrink-0 font-semibold tabular-nums">{pct(c.porcentaje)}</span>
                          </div>
                          <div className="mt-1 h-2 rounded-full bg-muted" aria-hidden>
                            <div className={cn('h-2 rounded-full', tonoLogro(c.porcentaje, umbral).barra)} style={{ width: `${c.porcentaje ?? 0}%` }} />
                          </div>
                          <p className="text-[11px] text-muted-foreground">{c.presentaron} de {c.convocados} convocatorias</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </Seccion>
              </div>
            </>
          )}

          {/* ───────────── 4. Comparar ───────────── */}
          {etapa === 'comparar' && (
            <>
              <p role="note" className="flex items-start gap-2 rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
                <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                {a.comparacion.advertencia}
              </p>
              <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
                <Seccion titulo="Evolución por momentos" descripcion="% de logro general y de los RA con más respuestas · eje en %." fuente={FUENTE_OBS} accion={<Provisional />}>
                  <GraficoTendencia tendencia={a.tendencia} umbral={umbral} />
                  {a.comparacion.variaciones.length > 0 && (
                    <ul className="space-y-1 text-sm">
                      {a.comparacion.variaciones.map((v) => (
                        <li key={`${v.desde}-${v.hasta}`} className="flex justify-between gap-2">
                          <span className="text-muted-foreground">{v.desde} → {v.hasta}</span>
                          <span className={cn('font-semibold tabular-nums', v.variacion_pp > 0 ? 'text-success' : v.variacion_pp < 0 ? 'text-destructive' : 'text-foreground')}>
                            {v.variacion_pp > 0 ? '+' : ''}{v.variacion_pp} pp
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Seccion>
                <Seccion titulo="Distribución de desempeño" descripcion="Notas 0-5 por nivel." fuente="notas por asignatura de intentos + tareas calificadas" accion={conFicha('aprobacion')}>
                  <NivelesDesempeno niveles={a.niveles} />
                </Seccion>
              </div>
              <div className="grid gap-6 lg:grid-cols-3">
                <Seccion titulo="Por programa" descripcion="% de logro" fuente={FUENTE_OBS}>
                  <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.comparacion.por_programa.map((x) => ({ ...x, aciertos: 0, titulo: x.nombre }))} />
                </Seccion>
                <Seccion titulo="Por semestre" descripcion="% de logro" fuente={FUENTE_OBS}>
                  <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.comparacion.por_semestre.map((x) => ({ ...x, aciertos: 0, titulo: x.nombre }))} />
                </Seccion>
                <Seccion titulo="Por momento" descripcion="% de logro" fuente={FUENTE_OBS}>
                  <BarrasLogro umbral={umbral} alAbrir={(f) => abrir(f)} filas={a.comparacion.por_momento.map((x) => ({ ...x, aciertos: 0, titulo: x.nombre }))} />
                </Seccion>
              </div>
              <Seccion titulo="Cobertura de RA obligatorios por momento" descripcion="RA obligatorios con evaluación publicada." fuente="ev_momentos_resultados, ev_evaluaciones_formales · LAIRN" accion={conFicha('cobertura_ra')}>
                {a.cobertura.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No hay momentos con estos filtros.</p>
                ) : (
                  <ul className="grid gap-3 md:grid-cols-2">
                    {a.cobertura.map((c) => (
                      <li key={c.momento} className="rounded-lg border border-border p-3">
                        <div className="flex items-start justify-between gap-2 text-sm">
                          <span className="font-medium text-foreground">{c.nombre} <span className="text-xs font-normal text-muted-foreground">· {c.programa} · sem. {c.semestre}</span></span>
                          <span className="shrink-0 tabular-nums">{c.obligatorios ? `${c.evaluados} / ${c.obligatorios}` : 'Sin RA obligatorios'}</span>
                        </div>
                        {c.sin_evaluar.length > 0 && (
                          <ul className="mt-2 space-y-1 text-xs text-destructive">
                            {c.sin_evaluar.map((r) => <li key={r.id}>Sin evaluar: {r.descripcion}</li>)}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </Seccion>
            </>
          )}

          {/* ───────────── 5. Conclusiones ───────────── */}
          {etapa === 'conclusiones' && (
            <>
              <Seccion titulo="Conclusiones descriptivas" descripcion="Se desprenden de las cifras de los pasos anteriores con los filtros aplicados.">
                <ol className="list-decimal space-y-2 pl-5 text-sm text-foreground">
                  {a.conclusiones.puntos.map((p) => <li key={p}>{p}</li>)}
                </ol>
              </Seccion>
              {a.hallazgos.filter((h) => h.tipo === 'atencion').length > 0 && (
                <Seccion titulo="Prioridades que se derivan de los hallazgos" descripcion="Las tres situaciones de mayor prioridad.">
                  <ul className="grid gap-3 lg:grid-cols-3">
                    {a.hallazgos.filter((h) => h.tipo === 'atencion').slice(0, 3).map((h, i) => (
                      <TarjetaHallazgo key={i} hallazgo={h} alAbrir={h.filtro ? () => abrir(h.filtro!, h.etapa) : undefined} />
                    ))}
                  </ul>
                </Seccion>
              )}
              <Seccion titulo="Limitaciones de este análisis" descripcion="Léelas antes de usar las cifras en un informe.">
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {a.conclusiones.limitaciones.map((l) => <li key={l}>{l}</li>)}
                </ul>
              </Seccion>
            </>
          )}

          {/* ───────────── 6. Evidencia y metodología ───────────── */}
          {etapa === 'evidencia' && (
            <>
              <Seccion titulo="Exportar este informe" descripcion="PDF y Excel con las mismas cifras, filtros, fecha de corte y aviso metodológico." accion={botonesExportar}>
                <p className="text-sm text-muted-foreground">Filtros aplicados: {Object.keys(filtros).length ? Object.entries(filtros).map(([k, v]) => `${k}=${v}`).join(', ') : 'ninguno (toda la institución)'}.</p>
              </Seccion>
              <Seccion titulo="Notas de las evaluaciones formales (escala 0-5)" descripcion="HU-11: los anulados por fraude no cuentan." fuente="notas por asignatura de intentos + tareas calificadas" accion={conFicha('notas')}>
                <Datos items={[['Resultados', ind.resultados], ['Estudiantes', ind.estudiantes], ['Promedio', ind.promedio === null ? '—' : ind.promedio.toFixed(2)], ['Desviación', ind.desviacion === null ? '—' : ind.desviacion.toFixed(2)], ['Sobre / bajo la media', `${ind.por_encima} / ${ind.por_debajo}`]]} />
                {ind.resultados > 0 && (
                  <ChartContainer config={configNotas} className="h-[220px] w-full">
                    <BarChart data={ind.distribucion}>
                      <CartesianGrid stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="rango" tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }} />
                      <YAxis allowDecimals={false} width={32} tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="cantidad" name="Resultados" fill="var(--color-cantidad)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                    </BarChart>
                  </ChartContainer>
                )}
                {datos.desglose.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{esInstitucion ? 'Programa' : 'Materia'}</TableHead>
                        <TableHead className="text-right">Estudiantes</TableHead>
                        <TableHead className="text-right">Promedio</TableHead>
                        <TableHead className="hidden text-right sm:table-cell">Desviación</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {datos.desglose.map((d) => (
                        <TableRow key={d.id}>
                          <TableCell className="whitespace-normal">{d.codigo} — {d.nombre}</TableCell>
                          <TableCell className="text-right tabular-nums">{d.estudiantes}</TableCell>
                          <TableCell className="text-right font-medium tabular-nums">{d.promedio?.toFixed(2) ?? '—'}</TableCell>
                          <TableCell className="hidden text-right tabular-nums sm:table-cell">{d.desviacion?.toFixed(2) ?? '—'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </Seccion>
              <div className="grid gap-6 lg:grid-cols-2">
                <Seccion titulo="Convocatoria y participación" fuente="inscripciones, ev_convocados_evaluacion, ev_asistencias_evaluacion · LAIRN" accion={conFicha('participacion')}>
                  <Datos items={[['Convocados', a.participacion.convocados], ['Iniciaron', a.participacion.iniciaron], ['Presentaron', a.participacion.presentaron], ['Anulados', a.participacion.anulados], ['Presentes en sala', a.participacion.con_control_asistencia ? `${a.participacion.presentes} de ${a.participacion.convocados_con_control}` : 'sin supervisión'], ['Evaluaciones', `${a.evaluaciones.presentadas} / ${a.evaluaciones.publicadas}`]]} />
                </Seccion>
                <Seccion titulo="Integridad académica" fuente="ev_incidentes_intento, ev_resoluciones_integridad · LAIRN" accion={conFicha('integridad')}>
                  <Datos items={[['Suspensiones', a.integridad.suspensiones], ['Anulaciones', a.integridad.anulaciones], ['Reactivaciones', a.integridad.reactivaciones], ['Suspendidas ahora', a.integridad.suspendidos_ahora]]} />
                </Seccion>
              </div>
              <Seccion titulo="Calidad y suficiencia de los datos" descripcion="Vacíos que limitan el análisis. Un vacío no es un resultado académico.">
                <ul className="divide-y divide-border text-sm">
                  {a.calidad_datos.map((c) => (
                    <li key={c.clave} className="py-2">
                      <span className="flex justify-between gap-2">
                        <span className="text-foreground">{c.titulo}</span>
                        <span className="shrink-0 font-semibold tabular-nums">{c.valor} / {c.total}</span>
                      </span>
                      <span className="block text-xs text-muted-foreground">{c.impacto}</span>
                    </li>
                  ))}
                </ul>
              </Seccion>
              <Seccion titulo="Fichas técnicas de los indicadores" descripcion="Definición, fórmula, fuente y limitaciones de cada cifra. Pulsa un indicador para ver su ficha completa.">
                <ul className="grid gap-2 md:grid-cols-2">
                  {fichas.map((f) => (
                    <li key={f.id}>
                      <button type="button" onClick={() => setFicha(f)} className="w-full rounded-lg border border-border p-3 text-left hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                        <span className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-foreground">
                          {f.nombre}
                          <Badge variant="outline" className="font-normal">{NIVEL_INDICADOR[f.nivel]}</Badge>
                          {f.provisional && <Badge variant="outline" className="border-warning/60 font-normal">Provisional</Badge>}
                        </span>
                        <span className="mt-0.5 block font-mono text-xs text-muted-foreground">{f.formula}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </Seccion>
              <Seccion titulo="Indicadores oficiales que no se pueden calcular con los datos actuales" descripcion="Se declaran en lugar de aproximarlos.">
                <ul className="divide-y divide-border text-sm">
                  {a.indicadores_no_disponibles.map((x) => (
                    <li key={x.nombre} className="py-2">
                      <span className="flex flex-wrap justify-between gap-2">
                        <span className="text-foreground">{x.nombre}</span>
                        <Badge variant="outline" className="font-normal">{x.referente}</Badge>
                      </span>
                      <span className="block text-xs text-muted-foreground">Falta: {x.falta}</span>
                    </li>
                  ))}
                </ul>
              </Seccion>
            </>
          )}

          {/* Navegación entre etapas */}
          <nav aria-label="Paso anterior y siguiente" className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-4">
            {indice > 0 ? (
              <Button variant="outline" onClick={() => irEtapa(ETAPAS[indice - 1].clave)}>
                <ArrowLeft className="mr-1.5 h-4 w-4" aria-hidden />
                {ETAPAS[indice - 1].titulo}
              </Button>
            ) : <span />}
            {indice < ETAPAS.length - 1 && (
              <Button onClick={() => irEtapa(ETAPAS[indice + 1].clave)}>
                Siguiente: {ETAPAS[indice + 1].titulo}
                <ArrowRight className="ml-1.5 h-4 w-4" aria-hidden />
              </Button>
            )}
          </nav>
        </div>
      ) : null}

      {!datos && !cargando && !error && (
        <Card><CardContent className="p-6 text-sm text-muted-foreground">Sin datos.</CardContent></Card>
      )}
      <DialogoFicha ficha={ficha} alCerrar={() => setFicha(null)} />
    </div>
  )
}
