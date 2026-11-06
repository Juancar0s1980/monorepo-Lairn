// Inicio del Coordinador (ADR-013), con datos reales de sus programas.
//
// - Cobertura de RA obligatorios por momento y evaluaciones por estado.
// - Próximas y abiertas evaluaciones (con supervisor).
// - Convocatoria → asistencia → participación.
// - Alertas tempranas abiertas, preguntas pendientes de validación por
//   asignatura (las valida el docente), docentes con cursos vinculados.
// - Integridad: suspendidos que esperan decisión.
// - Accesos directos a cada detalle. No abre nada que sea solo del
//   Administrador (programas, importación, desempeño por RA).
// Sin datos = estados vacíos que dicen qué falta; nunca cifras inventadas.

import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ArrowRight, BookOpenCheck, CalendarClock, GraduationCap, Loader2, ShieldAlert, Users } from 'lucide-react'
import { cn } from '@/lib/utils'
import { mensajeError } from '@/pages/academico/academico-utils'
import { TarjetaKpi } from '@/pages/reporte/componentes/graficos-reporte'
import { pct, tonoLogro } from '@/pages/reporte/reporte-utils'
import type { PanelCoordinador } from '@/types/panel-coordinador'

const TODOS = 'todos'
const formatoFecha = new Intl.DateTimeFormat('es-CO', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
const formatoHoy = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

function Seccion({
  titulo,
  descripcion,
  enlace,
  children,
}: {
  titulo: string
  descripcion?: string
  enlace?: { a: string; texto: string }
  children: React.ReactNode
}) {
  return (
    <Card className="min-w-0">
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
        <div>
          <CardTitle className="text-base">{titulo}</CardTitle>
          {descripcion && <CardDescription>{descripcion}</CardDescription>}
        </div>
        {enlace && (
          <Link to={enlace.a} className="flex shrink-0 items-center gap-1 text-sm text-primary hover:underline">
            {enlace.texto}
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        )}
      </CardHeader>
      <CardContent className="min-w-0">{children}</CardContent>
    </Card>
  )
}

function Vacio({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>
}

function Barra({ porcentaje, clase }: { porcentaje: number | null; clase: string }) {
  return (
    <div className="h-2 rounded-full bg-muted" aria-hidden>
      <div className={cn('h-2 rounded-full', clase)} style={{ width: `${Math.min(100, porcentaje ?? 0)}%` }} />
    </div>
  )
}

export default function PaginaDashboardCoordinador() {
  const [params, setParams] = useSearchParams()
  const programa = params.get('programa') ?? ''
  const [datos, setDatos] = useState<PanelCoordinador | null>(null)
  const [error, setError] = useState('')
  const [claveCargada, setClaveCargada] = useState<string | null>(null)
  const cargando = claveCargada !== programa
  const [hoy] = useState(() => {
    const texto = formatoHoy.format(new Date())
    return texto.charAt(0).toUpperCase() + texto.slice(1)
  })

  useEffect(() => {
    let activo = true
    api
      .get<PanelCoordinador>(`/evaluacion/panel-coordinador/${programa ? `?programa=${programa}` : ''}`)
      .then((r) => {
        if (activo) {
          setDatos(r.data)
          setError('')
        }
      })
      .catch((err: unknown) => activo && setError(mensajeError(err, 'No se pudo cargar el panel.')))
      .finally(() => activo && setClaveCargada(programa))
    return () => {
      activo = false
    }
  }, [programa])

  const items = [{ value: TODOS, label: 'Todos los programas' }, ...(datos?.programas ?? []).map((p) => ({ value: String(p.id), label: p.nombre }))]
  const obligatorios = datos?.momentos.reduce((s, m) => s + m.obligatorios, 0) ?? 0
  const evaluados = datos?.momentos.reduce((s, m) => s + m.evaluados, 0) ?? 0
  const coberturaTotal = obligatorios ? Math.round((1000 * evaluados) / obligatorios) / 10 : null

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Coordinación académica"
        titulo="Inicio"
        subtitulo={hoy}
        accion={
          <Select
            value={programa || TODOS}
            onValueChange={(v) => setParams(!v || v === TODOS ? {} : { programa: v })}
            items={items}
          >
            <SelectTrigger className="w-full sm:w-80" aria-label="Programa">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {items.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      {/* Accesos directos */}
      <nav aria-label="Accesos directos" className="flex flex-wrap gap-2">
        {[
          { a: '/academico', texto: 'Malla, competencias y momentos', icono: GraduationCap },
          { a: '/estudiantes', texto: 'Convocados e inscritos', icono: Users },
          { a: '/academico?tab=alertas', texto: 'Alertas tempranas', icono: ShieldAlert },
          { a: '/reporte-institucional', texto: 'Informe de resultados de aprendizaje', icono: BookOpenCheck },
        ].map((x) => (
          <Link
            key={x.a}
            to={x.a}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            <x.icono className="h-4 w-4 text-primary" aria-hidden />
            {x.texto}
          </Link>
        ))}
      </nav>

      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {!datos && cargando ? (
        <div className="flex min-h-[40vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando panel" />
        </div>
      ) : datos ? (
        <div className={cn('space-y-6 transition-opacity', cargando && 'opacity-60')}>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
            <TarjetaKpi
              titulo="Cobertura de RA"
              valor={pct(coberturaTotal)}
              tono={tonoLogro(coberturaTotal, 100).texto}
              detalle={obligatorios ? `${evaluados} de ${obligatorios} obligatorios con evaluación` : 'Sin RA obligatorios vinculados'}
            />
            <TarjetaKpi titulo="Evaluaciones abiertas" valor={String(datos.evaluaciones.abiertas)} detalle={`${datos.evaluaciones.publicadas} publicadas · ${datos.evaluaciones.borradores} borrador(es)`} />
            <TarjetaKpi titulo="Participación" valor={pct(datos.participacion.porcentaje_participacion)} detalle={`${datos.participacion.presentaron} de ${datos.participacion.convocados} convocados`} />
            <TarjetaKpi titulo="Alertas abiertas" valor={String(datos.alertas.abiertas)} tono={datos.alertas.abiertas ? 'text-warning' : undefined} detalle="alerta temprana" />
            <TarjetaKpi titulo="Preguntas pendientes" valor={String(datos.banco.pendientes)} tono={datos.banco.pendientes ? 'text-warning' : undefined} detalle={`${datos.banco.aprobadas} aprobadas en el banco`} />
            <TarjetaKpi
              titulo="Suspendidos"
              valor={String(datos.integridad.suspendidos_ahora)}
              tono={datos.integridad.suspendidos_ahora ? 'text-destructive' : undefined}
              detalle={`${datos.integridad.anulaciones} anulación(es) por fraude`}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Seccion titulo="Evaluaciones abiertas y próximas" descripcion="Publicadas que aún no cierran.">
              {datos.proximas.length === 0 ? (
                <Vacio>No hay evaluaciones publicadas pendientes de cierre. Se crean desde cada momento en Académico.</Vacio>
              ) : (
                <ul className="space-y-2">
                  {datos.proximas.map((e) => (
                    <li key={e.id}>
                      <Link
                        to={`/academico/momentos/${e.momento_id}/evaluaciones`}
                        className="flex items-start justify-between gap-2 rounded-lg border border-border p-3 transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                      >
                        <span className="min-w-0">
                          <span className="block text-sm font-medium text-foreground">{e.nombre}</span>
                          <span className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                            <CalendarClock className="h-3 w-3" aria-hidden />
                            {formatoFecha.format(new Date(e.fecha_inicio))} → {formatoFecha.format(new Date(e.fecha_fin))}
                          </span>
                          <span className="block text-xs text-muted-foreground">
                            {e.programa} · {e.momento} · {e.supervisor ? `Supervisa ${e.supervisor}` : 'Sin supervisor en sala'}
                          </span>
                        </span>
                        <Badge className={cn('shrink-0 border-transparent', e.abierta ? 'bg-success/10 text-success' : 'bg-primary/10 text-primary')}>
                          {e.abierta ? 'Abierta' : 'Próxima'}
                        </Badge>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Seccion>

            <Seccion titulo="Cobertura de RA por momento" descripcion="RA obligatorios con evaluación publicada.">
              {datos.momentos.length === 0 ? (
                <Vacio>No hay momentos de evaluación activos. Créalos en Académico → Momentos.</Vacio>
              ) : (
                <ul className="space-y-3">
                  {datos.momentos.map((m) => {
                    const tono = tonoLogro(m.porcentaje, 100)
                    return (
                      <li key={m.momento}>
                        <Link to={`/academico/momentos/${m.momento}/evaluaciones`} className="block rounded-lg p-1 hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                          <span className="flex items-center justify-between gap-2 text-sm">
                            <span className="min-w-0 truncate text-foreground">
                              {m.nombre} <span className="text-xs text-muted-foreground">· {m.programa} · sem. {m.semestre}</span>
                            </span>
                            <span className="shrink-0 font-semibold tabular-nums">
                              {m.obligatorios ? `${m.evaluados}/${m.obligatorios}` : 'sin RA obligatorios'}
                            </span>
                          </span>
                          <Barra porcentaje={m.porcentaje} clase={tono.barra} />
                          <span className="mt-0.5 block text-[11px] text-muted-foreground">
                            {m.publicadas} publicada(s) · {m.borradores} borrador(es)
                            {m.sin_evaluar.length > 0 && ` · sin evaluar: ${m.sin_evaluar.map((r) => r.descripcion).join('; ')}`}
                          </span>
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </Seccion>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Seccion titulo="Convocatoria y participación" descripcion="Evaluaciones publicadas." enlace={{ a: '/estudiantes', texto: 'Ver estudiantes' }}>
              {datos.participacion.convocados === 0 ? (
                <Vacio>Aún no hay estudiantes convocados: vincula cursos a las asignaturas en la malla o carga convocados en una evaluación.</Vacio>
              ) : (
                <ul className="space-y-3">
                  {[
                    { texto: 'Convocados', valor: datos.participacion.convocados, base: datos.participacion.convocados },
                    { texto: 'Iniciaron', valor: datos.participacion.iniciaron, base: datos.participacion.convocados },
                    { texto: 'Presentaron', valor: datos.participacion.presentaron, base: datos.participacion.convocados },
                    ...(datos.participacion.con_control_asistencia
                      ? [{ texto: 'Presentes en sala (con supervisor)', valor: datos.participacion.presentes, base: datos.participacion.convocados_con_control }]
                      : []),
                  ].map((x) => {
                    const p = x.base ? (100 * x.valor) / x.base : null
                    return (
                      <li key={x.texto}>
                        <span className="flex justify-between text-sm">
                          <span className="text-foreground">{x.texto}</span>
                          <span className="font-semibold tabular-nums">
                            {x.valor} <span className="text-xs font-normal text-muted-foreground">({pct(p === null ? null : Math.round(p * 10) / 10)})</span>
                          </span>
                        </span>
                        <Barra porcentaje={p} clase="bg-primary" />
                      </li>
                    )
                  })}
                </ul>
              )}
            </Seccion>

            <Seccion titulo="Alertas tempranas abiertas" descripcion="Estudiantes o cursos con varias actividades bajas." enlace={{ a: '/academico?tab=alertas', texto: 'Atender' }}>
              {datos.alertas.recientes.length === 0 ? (
                <Vacio>No hay alertas abiertas.</Vacio>
              ) : (
                <ul className="space-y-2">
                  {datos.alertas.recientes.map((a) => (
                    <li key={a.id} className="flex items-start justify-between gap-2 rounded-lg border border-border p-3 text-sm">
                      <span className="min-w-0">
                        <span className="block text-foreground">{a.estudiante ?? a.asignatura}</span>
                        <span className="block text-xs text-muted-foreground">{a.tipo === 'estudiante' ? 'Estudiante' : 'Curso'} · {a.programa}</span>
                      </span>
                      <Badge className="shrink-0 border-transparent bg-warning/15 text-foreground">
                        {a.actividades_bajas} de {a.total_actividades} bajas
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Seccion>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Seccion titulo="Banco de preguntas por asignatura" descripcion="Las pendientes las valida el docente de la asignatura (HU-05).">
              {datos.banco.por_asignatura.length === 0 ? (
                <Vacio>Aún no hay preguntas en el banco para este programa.</Vacio>
              ) : (
                <ul className="space-y-3">
                  {datos.banco.por_asignatura.map((b) => {
                    const total = b.pendientes + b.aprobadas
                    return (
                      <li key={b.asignatura}>
                        <span className="flex items-center justify-between gap-2 text-sm">
                          <span className="min-w-0 truncate text-foreground">
                            <span className="mr-1.5 rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">{b.codigo}</span>
                            {b.nombre}
                          </span>
                          <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                            <strong className={b.pendientes ? 'text-warning' : 'text-foreground'}>{b.pendientes}</strong> pend. · {b.aprobadas} aprob.
                          </span>
                        </span>
                        <Barra porcentaje={total ? (100 * b.aprobadas) / total : null} clase="bg-success" />
                      </li>
                    )
                  })}
                </ul>
              )}
            </Seccion>

            <Seccion
              titulo="Docentes con cursos vinculados"
              descripcion={`${datos.docentes.asignaturas_con_curso} asignatura(s) con curso · ${datos.docentes.asignaturas_sin_curso} sin curso vinculado`}
              enlace={{ a: '/academico', texto: 'Ir a la malla' }}
            >
              {datos.docentes.docentes.length === 0 ? (
                <Vacio>Ninguna asignatura tiene un curso vinculado: sin eso no hay convocatoria por curso. Vincúlalas en la pestaña Malla.</Vacio>
              ) : (
                <ul className="divide-y divide-border">
                  {datos.docentes.docentes.map((d) => (
                    <li key={d.id} className="flex items-start justify-between gap-2 py-2 text-sm">
                      <span className="min-w-0">
                        <span className="block font-medium text-foreground">{d.nombre}</span>
                        <span className="block text-xs break-all text-muted-foreground">{d.email}</span>
                      </span>
                      <span className="flex shrink-0 flex-wrap justify-end gap-1">
                        {d.asignaturas.map((a) => (
                          <Badge key={a} variant="outline" className="font-mono text-[11px] font-normal">{a}</Badge>
                        ))}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Seccion>
          </div>

          <Seccion titulo="Integridad académica" descripcion="Incidentes durante la presentación (ADR-010).">
            <div className="space-y-4">
              <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                {[
                  ['Suspendidos ahora', datos.integridad.suspendidos_ahora],
                  ['Suspensiones', datos.integridad.suspensiones],
                  ['Reactivaciones', datos.integridad.reactivaciones],
                  ['Anulaciones por fraude', datos.integridad.anulaciones],
                ].map(([t, v]) => (
                  <div key={String(t)} className="rounded-lg bg-muted/40 p-3">
                    <dt className="text-xs text-muted-foreground">{t}</dt>
                    <dd className="text-lg font-semibold tabular-nums text-foreground">{v}</dd>
                  </div>
                ))}
              </dl>
              {datos.integridad.suspendidos.length > 0 ? (
                <ul className="space-y-2">
                  {datos.integridad.suspendidos.map((s, i) => (
                    <li key={i}>
                      <Link
                        to={`/academico/momentos/${s.momento_id}/evaluaciones`}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm hover:border-destructive focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                      >
                        <span className="min-w-0">
                          <span className="block font-medium text-foreground">{s.estudiante}</span>
                          <span className="block text-xs text-muted-foreground">{s.nombre} · decide: {s.decide}</span>
                        </span>
                        <Badge className="border-transparent bg-destructive text-white">Esperando decisión</Badge>
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="flex items-center gap-2 text-sm text-muted-foreground">
                  <BookOpenCheck className="h-4 w-4 text-success" aria-hidden />
                  Ningún estudiante espera decisión por integridad.
                </p>
              )}
            </div>
          </Seccion>
        </div>
      ) : null}
    </div>
  )
}
