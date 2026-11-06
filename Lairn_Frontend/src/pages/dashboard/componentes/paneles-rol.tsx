// Secciones de evaluación de resultados de aprendizaje en el inicio de cada rol
// (ADR-014). Se insertan en los tableros existentes sin reescribirlos.
// - PanelAdminEvaluacion: estado de la plataforma (usuarios por rol,
//   importaciones, cargues, evaluaciones activas, integridad).
// - PanelDocenteEvaluacion: sus asignaturas, banco, tareas, supervisiones y
//   resultados agregados por RA y por pregunta (métrica provisional).
// - PanelEstudianteEvaluacion: pendientes (evaluaciones convocadas, tareas con
//   plazo) e historial. HU-07: sin nota de la evaluación formal.
// Cada uno carga su propio endpoint; si falla, muestra el error sin romper la página.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowRight, CalendarClock, ClipboardCheck, FileCheck2, Info, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { mensajeError } from '@/pages/academico/academico-utils'
import { BarrasLogro, TarjetaKpi } from '@/pages/reporte/componentes/graficos-reporte'
import { pct, tonoLogro } from '@/pages/reporte/reporte-utils'
import type { PanelAdmin, PanelDocente, PanelEstudiante } from '@/types/paneles-rol'

const formatoFecha = new Intl.DateTimeFormat('es-CO', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
const formatoDia = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })

function usePanel<T>(url: string) {
  const [datos, setDatos] = useState<T | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let activo = true
    api
      .get<T>(url)
      .then((r) => activo && setDatos(r.data))
      .catch((err: unknown) => activo && setError(mensajeError(err, 'No se pudo cargar el resumen.')))
    return () => {
      activo = false
    }
  }, [url])
  return { datos, error }
}

function Seccion({ titulo, descripcion, enlace, children }: { titulo: string; descripcion?: string; enlace?: { a: string; texto: string }; children: React.ReactNode }) {
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

function Estado({ error, cargando }: { error: string; cargando: boolean }) {
  if (error) return <p role="alert" className="text-sm text-destructive">{error}</p>
  if (cargando)
    return (
      <div className="flex justify-center py-6">
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  return null
}

const Vacio = ({ children }: { children: React.ReactNode }) => <p className="text-sm text-muted-foreground">{children}</p>

// ------------------------------------------------------------------ Administrador

export function PanelAdminEvaluacion() {
  const { datos, error } = usePanel<PanelAdmin>('/evaluacion/panel-admin/')
  if (!datos) return <Estado error={error} cargando />
  const totalUsuarios = datos.usuarios.reduce((s, u) => s + u.activos, 0)
  return (
    <section aria-label="Estado de la plataforma" className="space-y-4">
      <h2 className="font-heading text-xl text-foreground">Estado de la plataforma</h2>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <TarjetaKpi titulo="Usuarios activos" valor={String(totalUsuarios)} detalle={datos.usuarios.map((u) => `${u.rol}: ${u.activos}`).join(' · ')} />
        <TarjetaKpi titulo="Evaluaciones abiertas" valor={String(datos.evaluaciones.abiertas)} detalle={`${datos.evaluaciones.publicadas} publicadas`} />
        <TarjetaKpi titulo="Convocados por cargue" valor={String(datos.convocados_por_cargue)} />
        <TarjetaKpi titulo="Alertas abiertas" valor={String(datos.alertas_abiertas)} tono={datos.alertas_abiertas ? 'text-warning' : undefined} />
        <TarjetaKpi
          titulo="Integridad"
          valor={`${datos.integridad.suspendidos_ahora} / ${datos.integridad.anulaciones}`}
          tono={datos.integridad.suspendidos_ahora ? 'text-destructive' : undefined}
          detalle="suspendidos ahora / anulaciones"
        />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Seccion titulo="Importaciones recientes" descripcion="Integración institucional (HU-03)." enlace={{ a: '/academico?tab=integracion', texto: 'Importar' }}>
          {datos.importaciones.length === 0 ? (
            <Vacio>Aún no hay importaciones.</Vacio>
          ) : (
            <ul className="divide-y divide-border text-sm">
              {datos.importaciones.map((i) => (
                <li key={i.id} className="py-2">
                  <span className="flex justify-between gap-2">
                    <span className="truncate text-foreground">{i.entidad}</span>
                    <Badge variant="outline" className="shrink-0 font-normal">{i.modo}</Badge>
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {formatoDia.format(new Date(i.creado_en))} · {i.creados} creados · {i.actualizados} act. · {i.omitidos} omit.
                    {i.errores > 0 && <span className="text-destructive"> · {i.errores} error(es)</span>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
        <Seccion titulo="Cargues documentales" descripcion={Object.entries(datos.cargues.por_estado).map(([e, n]) => `${e}: ${n}`).join(' · ') || 'Sin cargues'}>
          {datos.cargues.recientes.length === 0 ? (
            <Vacio>Aún no hay cargues documentales.</Vacio>
          ) : (
            <ul className="divide-y divide-border text-sm">
              {datos.cargues.recientes.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-2 py-2">
                  <span className="min-w-0">
                    <span className="block truncate text-foreground">{c.nombre_archivo}</span>
                    <span className="block text-xs text-muted-foreground">{c.tipo}{c.programa && ` · ${c.programa}`}</span>
                  </span>
                  <Badge variant="outline" className="shrink-0 font-normal">{c.estado}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
        <Seccion titulo="Evaluaciones abiertas ahora">
          {datos.abiertas.length === 0 ? (
            <Vacio>No hay evaluaciones abiertas en este momento.</Vacio>
          ) : (
            <ul className="space-y-2 text-sm">
              {datos.abiertas.map((e) => (
                <li key={e.id}>
                  <Link to={`/academico/momentos/${e.momento_id}/evaluaciones`} className="block rounded-lg border border-border p-2.5 hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                    <span className="block text-foreground">{e.nombre}</span>
                    <span className="block text-xs text-muted-foreground">
                      {e.programa} · cierra {formatoFecha.format(new Date(e.fecha_fin))} · {e.supervisor ?? 'sin supervisor'}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {datos.integridad.suspendidos.length > 0 && (
            <p className="mt-3 rounded-lg bg-destructive/10 p-2 text-xs text-destructive">
              {datos.integridad.suspendidos.length} estudiante(s) suspendido(s) esperan decisión.
            </p>
          )}
        </Seccion>
      </div>
    </section>
  )
}

// ------------------------------------------------------------------------ Docente

export function PanelDocenteEvaluacion() {
  const { datos, error } = usePanel<PanelDocente>('/evaluacion/docente/panel/')
  if (!datos) return <Estado error={error} cargando />
  if (datos.asignaturas.length === 0 && datos.supervisiones.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-start gap-2 p-4 text-sm text-muted-foreground">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          Ninguna asignatura de la malla está vinculada a tus cursos todavía. Cuando el coordinador la vincule, aquí verás tu banco de
          preguntas, tareas y resultados por resultado de aprendizaje.
        </CardContent>
      </Card>
    )
  }
  const r = datos.resultados
  return (
    <section aria-label="Evaluación de resultados de aprendizaje" className="space-y-4">
      <h2 className="font-heading text-xl text-foreground">Evaluación de resultados de aprendizaje</h2>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <TarjetaKpi titulo="Logro en mis asignaturas" valor={pct(r.general?.porcentaje)} tono={tonoLogro(r.general?.porcentaje, r.umbral_logro_porcentaje).texto} detalle={r.general ? `n = ${r.general.presentadas} respuestas` : 'Sin evaluaciones presentadas'} />
        <TarjetaKpi titulo="Preguntas pendientes" valor={String(datos.banco.pendiente)} tono={datos.banco.pendiente ? 'text-warning' : undefined} detalle={`${datos.banco.aprobada} aprobadas · ${datos.banco.descartada} descartadas`} />
        <TarjetaKpi titulo="Entregas sin calificar" valor={String(datos.tareas.entregas_sin_calificar)} tono={datos.tareas.entregas_sin_calificar ? 'text-warning' : undefined} detalle={`${datos.tareas.publicadas} tarea(s) publicadas · ${datos.tareas.borradores} borrador(es)`} />
        <TarjetaKpi titulo="Supervisiones" valor={String(datos.supervisiones.length)} detalle="próximas o abiertas" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Seccion titulo="Logro por resultado de aprendizaje" descripcion={r.aviso}>
          {r.por_ra.length === 0 ? (
            <Vacio>Aún no hay evaluaciones formales presentadas con preguntas de tus asignaturas.</Vacio>
          ) : (
            <BarrasLogro umbral={r.umbral_logro_porcentaje} filas={r.por_ra.map((x) => ({ ...x, titulo: x.descripcion, etiqueta: x.asignatura }))} />
          )}
        </Seccion>
        <Seccion titulo="Preguntas con mayor % de error" descripcion="Útil para revisar enseñanza o redacción.">
          {r.preguntas_error.length === 0 ? (
            <Vacio>Sin datos todavía.</Vacio>
          ) : (
            <ul className="space-y-2">
              {r.preguntas_error.map((q) => {
                const tono = tonoLogro(100 - q.porcentaje_error, r.umbral_logro_porcentaje)
                return (
                  <li key={q.pregunta} className="flex items-start justify-between gap-2 rounded-lg border border-border p-2.5 text-sm">
                    <span className="min-w-0">
                      <span className="line-clamp-2 text-foreground">{q.enunciado}</span>
                      <span className="text-xs text-muted-foreground">{q.asignatura} · n={q.presentadas}</span>
                    </span>
                    <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-semibold', tono.fondo, tono.texto)}>{pct(q.porcentaje_error)} error</span>
                  </li>
                )
              })}
            </ul>
          )}
        </Seccion>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Seccion titulo="Banco por asignatura" enlace={{ a: '/banco-preguntas', texto: 'Validar' }}>
          <ul className="divide-y divide-border text-sm">
            {datos.asignaturas.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-2 py-2">
                <span className="min-w-0 truncate text-foreground">
                  <span className="mr-1.5 font-mono text-[11px] text-muted-foreground">{a.codigo}</span>
                  {a.nombre}
                </span>
                <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                  <strong className={a.preguntas.pendiente ? 'text-warning' : 'text-foreground'}>{a.preguntas.pendiente}</strong> pend. · {a.preguntas.aprobada} aprob.
                </span>
              </li>
            ))}
          </ul>
        </Seccion>
        <Seccion titulo="Tareas con plazo próximo" enlace={{ a: '/tareas', texto: 'Ver tareas' }}>
          {datos.tareas.proximas.length === 0 ? (
            <Vacio>No hay tareas publicadas con plazo abierto.</Vacio>
          ) : (
            <ul className="space-y-2 text-sm">
              {datos.tareas.proximas.map((t) => (
                <li key={t.id} className="rounded-lg border border-border p-2.5">
                  <span className="block text-foreground">{t.titulo}</span>
                  <span className="block text-xs text-muted-foreground">
                    {t.asignatura} · vence {formatoFecha.format(new Date(t.fecha_limite))} · {t.entregas} entrega(s)
                    {t.sin_calificar > 0 && <span className="text-warning"> · {t.sin_calificar} sin calificar</span>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
        <Seccion titulo="Supervisiones próximas" enlace={{ a: '/supervision', texto: 'Llamado a lista' }}>
          {datos.supervisiones.length === 0 ? (
            <Vacio>No tienes evaluaciones asignadas para supervisar.</Vacio>
          ) : (
            <ul className="space-y-2 text-sm">
              {datos.supervisiones.map((s) => (
                <li key={s.id}>
                  <Link to={`/supervision/${s.id}`} className="flex items-start justify-between gap-2 rounded-lg border border-border p-2.5 hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                    <span className="min-w-0">
                      <span className="block text-foreground">{s.nombre}</span>
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <CalendarClock className="h-3 w-3" aria-hidden />
                        {formatoFecha.format(new Date(s.fecha_inicio))}
                      </span>
                    </span>
                    <Badge className={cn('shrink-0 border-transparent', s.abierta ? 'bg-success/10 text-success' : 'bg-primary/10 text-primary')}>
                      {s.abierta ? 'Abierta' : 'Próxima'}
                    </Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
      </div>
    </section>
  )
}

// --------------------------------------------------------------------- Estudiante

function etiquetaPendiente(e: PanelEstudiante['pendientes']['evaluaciones'][number]): { texto: string; clase: string } {
  if (e.intento === 'suspendido') return { texto: 'Suspendida', clase: 'bg-destructive/10 text-destructive' }
  if (e.intento === 'en_curso') return { texto: 'En curso', clase: 'bg-warning/15 text-foreground' }
  if (!e.activa) return { texto: 'Programada', clase: 'bg-muted text-muted-foreground' }
  if (e.requiere_asistencia && e.asistencia !== 'presente' && e.asistencia !== 'tarde')
    return { texto: 'Esperando llamado a lista', clase: 'bg-muted text-muted-foreground' }
  return { texto: 'Disponible', clase: 'bg-success/10 text-success' }
}

export function PanelEstudianteEvaluacion() {
  const { datos, error } = usePanel<PanelEstudiante>('/evaluacion/estudiante/panel/')
  if (!datos) return <Estado error={error} cargando />
  return (
    <section aria-label="Mis evaluaciones y tareas" className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <TarjetaKpi titulo="Evaluaciones pendientes" valor={String(datos.resumen.evaluaciones_pendientes)} tono={datos.resumen.evaluaciones_pendientes ? 'text-primary' : undefined} />
        <TarjetaKpi titulo="Tareas pendientes" valor={String(datos.resumen.tareas_pendientes)} tono={datos.resumen.tareas_pendientes ? 'text-warning' : undefined} />
        <TarjetaKpi titulo="Evaluaciones presentadas" valor={String(datos.resumen.evaluaciones_presentadas)} />
        <TarjetaKpi titulo="Tareas entregadas" valor={String(datos.resumen.tareas_entregadas)} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Seccion titulo="Próximas evaluaciones" enlace={{ a: '/mis-evaluaciones', texto: 'Ver todas' }}>
          {datos.pendientes.evaluaciones.length === 0 ? (
            <Vacio>No tienes evaluaciones formales pendientes.</Vacio>
          ) : (
            <ul className="space-y-2">
              {datos.pendientes.evaluaciones.map((e) => {
                const estado = etiquetaPendiente(e)
                const destino = e.tipo === 'tarea' && e.tarea ? `/mis-tareas/${e.tarea}` : `/mis-evaluaciones/${e.id}`
                return (
                  <li key={e.id}>
                    <Link to={destino} className="flex items-start justify-between gap-2 rounded-lg border border-border p-3 hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                      <span className="min-w-0">
                        <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                          <ClipboardCheck className="h-4 w-4 text-primary" aria-hidden />
                          {e.nombre}
                        </span>
                        <span className="block text-xs text-muted-foreground">
                          {e.momento} · {formatoFecha.format(new Date(e.fecha_inicio))} · {e.duracion_minutos} min
                        </span>
                      </span>
                      <Badge className={cn('shrink-0 border-transparent', estado.clase)}>{estado.texto}</Badge>
                    </Link>
                  </li>
                )
              })}
            </ul>
          )}
        </Seccion>
        <Seccion titulo="Tareas con plazo" enlace={{ a: '/mis-tareas', texto: 'Ver todas' }}>
          {datos.pendientes.tareas.length === 0 ? (
            <Vacio>No tienes tareas pendientes de entrega.</Vacio>
          ) : (
            <ul className="space-y-2">
              {datos.pendientes.tareas.map((t) => (
                <li key={t.id}>
                  <Link to={`/mis-tareas/${t.id}`} className="flex items-start justify-between gap-2 rounded-lg border border-border p-3 hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                    <span className="min-w-0">
                      <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                        <FileCheck2 className="h-4 w-4 text-primary" aria-hidden />
                        {t.titulo}
                      </span>
                      <span className="block text-xs text-muted-foreground">{t.asignatura} · vence {formatoFecha.format(new Date(t.fecha_limite))}</span>
                    </span>
                    <Badge className={cn('shrink-0 border-transparent', t.plazo === 'tardia' ? 'bg-warning/15 text-foreground' : 'bg-primary/10 text-primary')}>
                      {t.plazo === 'tardia' ? 'Con retraso' : 'Abierta'}
                    </Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
      </div>
      <Seccion titulo="Historial" descripcion="Las evaluaciones formales no muestran nota (HU-07); las tareas calificadas sí.">
        {datos.historial.evaluaciones.length === 0 && datos.historial.tareas.length === 0 ? (
          <Vacio>Aún no has presentado evaluaciones ni entregado tareas.</Vacio>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            <ul className="divide-y divide-border text-sm">
              {datos.historial.evaluaciones.map((e) => (
                <li key={e.id} className="flex items-center justify-between gap-2 py-2">
                  <span className="min-w-0">
                    <span className="block truncate text-foreground">{e.nombre}</span>
                    <span className="block text-xs text-muted-foreground">{e.momento} · {formatoDia.format(new Date(e.enviado_en))}</span>
                  </span>
                  <Badge className={cn('shrink-0 border-transparent', e.anulada ? 'bg-destructive/10 text-destructive' : 'bg-success/10 text-success')}>
                    {e.anulada ? 'Anulada' : e.envio_automatico ? 'Enviada (tiempo)' : 'Enviada'}
                  </Badge>
                </li>
              ))}
            </ul>
            <ul className="divide-y divide-border text-sm">
              {datos.historial.tareas.map((t) => (
                <li key={t.id} className="flex items-center justify-between gap-2 py-2">
                  <span className="min-w-0">
                    <span className="block truncate text-foreground">{t.titulo}</span>
                    <span className="block text-xs text-muted-foreground">
                      {t.asignatura} · {formatoDia.format(new Date(t.enviada_en))}
                      {t.con_retraso && ' · con retraso'}
                    </span>
                  </span>
                  <span className="shrink-0 text-sm font-semibold tabular-nums">{t.calificada ? `${t.nota} / 5` : <span className="text-xs font-normal text-muted-foreground">sin calificar</span>}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Seccion>
    </section>
  )
}
