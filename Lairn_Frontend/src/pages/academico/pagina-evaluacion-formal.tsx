// Evaluación formal de un momento (HU-06), para Administrador y Coordinador.
//
// 1. Datos: nombre, instrucciones, tipo, ventana de disponibilidad y duración.
// 2. Preguntas: por cada RA del momento, preguntas APROBADAS del banco oficial
//    (las ya usadas en laboratorio no aparecen). Se advierte si un RA
//    obligatorio queda sin preguntas.
// Horario: fecha, hora, duración y tolerancia; el cierre se calcula solo
// (`componentes/horario-evaluacion.tsx`).
// 3. Guardar como borrador o publicar (publicada = no editable).
// Tipo "tarea" (HU-06.4): en lugar de preguntas se elige una tarea publicada
// por el docente cuyo RA está vinculado al momento (HU-08B).
// 4. Supervisión en sala, convocados y seguimiento en vivo (ADR-009), también
//    con la evaluación publicada: ver `componentes/panel-supervision.tsx`.

import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { AlertTriangle, ArrowLeft, CheckCircle2, FileCheck2, Loader2, Lock, Plus, Save, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EvaluacionFormal } from '@/types/evaluacion-formal'
import { useEvaluacionFormal } from './use-evaluacion-formal'
import { PanelSupervision } from './componentes/panel-supervision'
import { HorarioEvaluacion } from './componentes/horario-evaluacion'

const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

const TIPOS = [
  {
    valor: 'cuestionario' as const,
    titulo: 'Selección múltiple',
    descripcion: 'Preguntas aprobadas del banco, única respuesta.',
    icono: CheckCircle2,
  },
  {
    valor: 'tarea' as const,
    titulo: 'Tarea con entrega',
    descripcion: 'Una tarea publicada por el docente, con plazo y rúbrica.',
    icono: FileCheck2,
  },
]

function TarjetaEvaluacion({ e, activa, alAbrir }: { e: EvaluacionFormal; activa: boolean; alAbrir: () => void }) {
  return (
    <button
      type="button"
      onClick={alAbrir}
      aria-current={activa ? 'true' : undefined}
      className={cn(
        'w-full rounded-xl border p-3 text-left transition-colors hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
        activa ? 'border-primary bg-primary/5' : 'border-border',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-medium text-foreground">{e.nombre}</span>
        <Badge
          className={cn(
            'shrink-0 border-transparent',
            e.estado === 'publicada' ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground',
          )}
        >
          {e.estado === 'publicada' ? 'Publicada' : 'Borrador'}
        </Badge>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {formatoFecha.format(new Date(e.fecha_inicio))} → {formatoFecha.format(new Date(e.fecha_fin))}
      </p>
      <p className="text-xs text-muted-foreground">
        {e.tipo === 'tarea'
          ? `Tarea: ${e.tarea_titulo ?? 'sin elegir'}`
          : `${e.total_preguntas} pregunta${e.total_preguntas === 1 ? '' : 's'}`}{' '}
        · {e.duracion_minutos} min
      </p>
      {e.supervisor_nombre && <p className="text-xs text-muted-foreground">Supervisor: {e.supervisor_nombre}</p>}
    </button>
  )
}

export default function PaginaEvaluacionFormal() {
  const { momentoId = '' } = useParams()
  const ef = useEvaluacionFormal(momentoId)
  const [confirmarPublicar, setConfirmarPublicar] = useState(false)

  if (ef.cargando) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  const volver = (
    <Link to="/academico" className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Volver a configuración académica
    </Link>
  )

  if (ef.errorCarga || !ef.banco) {
    return (
      <div className="space-y-4">
        {volver}
        <p role="alert" className="text-sm text-destructive">
          {ef.errorCarga || 'No se encontró el momento.'}
        </p>
      </div>
    )
  }

  const { banco } = ef
  const editando = ef.seleccionadaId !== null
  // RA obligatorios sin ninguna pregunta en la selección actual (aún sin guardar).
  const esTarea = ef.form.tipo === 'tarea'
  const tareaElegida = banco.tareas.find((t) => String(t.id) === ef.form.tarea)
  const obligatoriosSinPreguntas = banco.resultados.filter((r) =>
    esTarea
      ? r.obligatorio && tareaElegida?.resultado_id !== r.resultado.id
      : r.obligatorio && !r.preguntas.some((p) => ef.preguntasElegidas.includes(p.id)),
  )
  const listaParaPublicar = esTarea ? !!tareaElegida : ef.preguntasElegidas.length > 0

  return (
    <div className="space-y-6">
      {volver}
      <EncabezadoPagina
        eyebrow="Evaluación formal"
        titulo={banco.momento.nombre}
        subtitulo={`Semestre ${banco.momento.semestre} · ${banco.resultados.length} resultado(s) de aprendizaje vinculados`}
        accion={
          <Button onClick={ef.nueva}>
            <Plus className="mr-1.5 h-4 w-4" aria-hidden />
            Nueva evaluación
          </Button>
        }
      />

      {banco.resultados.length === 0 && (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Este momento no tiene resultados de aprendizaje vinculados. Vincúlalos primero en la pestaña
            Momentos (botón "Vincular resultados").
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        {/* Evaluaciones del momento */}
        <section aria-label="Evaluaciones del momento" className="space-y-2">
          {ef.evaluaciones.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aún no hay evaluaciones para este momento.</p>
          ) : (
            ef.evaluaciones.map((e) => (
              <TarjetaEvaluacion key={e.id} e={e} activa={ef.seleccionadaId === e.id} alAbrir={() => void ef.abrir(e)} />
            ))
          )}
        </section>

        {!editando ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Elige una evaluación de la lista o crea una nueva para definir sus fechas y preguntas.
            </CardContent>
          </Card>
        ) : (
          <div className="min-w-0 space-y-4">
            {ef.soloLectura && (
              <p className="flex items-center gap-2 rounded-lg bg-muted p-3 text-sm text-foreground">
                <Lock className="h-4 w-4" aria-hidden />
                Esta evaluación está publicada: ya no se puede modificar.
              </p>
            )}

            {/* 1. Datos */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">1. Datos de la evaluación</CardTitle>
                <CardDescription>Cuándo empieza, cuánto dura cada intento y cuánto margen hay para llegar tarde.</CardDescription>
              </CardHeader>
              <CardContent>
                <fieldset disabled={ef.soloLectura} className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="ef-nombre">
                      Nombre <span className="text-destructive" aria-hidden="true">*</span>
                    </Label>
                    <Input
                      id="ef-nombre"
                      value={ef.form.nombre}
                      placeholder="Ej.: Evaluación formal Momento 1 — 2026-2"
                      onChange={(e) => ef.setForm({ ...ef.form, nombre: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="ef-instrucciones">Instrucciones para el estudiante</Label>
                    <Textarea
                      id="ef-instrucciones"
                      value={ef.form.instrucciones}
                      onChange={(e) => ef.setForm({ ...ef.form, instrucciones: e.target.value })}
                    />
                  </div>
                  <div role="radiogroup" aria-label="Tipo de evaluación" className="grid gap-2 sm:grid-cols-2">
                    {TIPOS.map((t) => {
                      const activo = ef.form.tipo === t.valor
                      return (
                        <button
                          key={t.valor}
                          type="button"
                          role="radio"
                          aria-checked={activo}
                          onClick={() => ef.setForm({ ...ef.form, tipo: t.valor })}
                          className={cn(
                            'rounded-xl border p-3 text-left transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                            activo ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted',
                          )}
                        >
                          <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                            <t.icono className={cn('h-4 w-4', activo && 'text-primary')} aria-hidden />
                            {t.titulo}
                          </span>
                          <span className="block text-xs text-muted-foreground">{t.descripcion}</span>
                        </button>
                      )
                    })}
                  </div>
                  <HorarioEvaluacion
                    key={String(ef.seleccionadaId)}
                    valor={ef.form}
                    onChange={(cambio) => ef.setForm({ ...ef.form, ...cambio })}
                  />
                </fieldset>
              </CardContent>
            </Card>

            {/* 2a. Tarea a evaluar (tipo tarea) */}
            {esTarea && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">2. Tarea que se evalúa</CardTitle>
                  <CardDescription>
                    Solo aparecen tareas publicadas por los docentes cuyo resultado de aprendizaje está vinculado a este momento.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {banco.tareas.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No hay tareas publicadas para los RA de este momento. El docente las crea en su menú "Tareas".
                    </p>
                  ) : (
                    <Select
                      value={ef.form.tarea}
                      onValueChange={(v) => ef.setForm({ ...ef.form, tarea: v ?? '' })}
                      items={banco.tareas.map((t) => ({ value: String(t.id), label: `${t.asignatura} — ${t.titulo}` }))}
                      disabled={ef.soloLectura}
                    >
                      <SelectTrigger className="w-full" aria-label="Tarea que se evalúa">
                        <SelectValue placeholder="Elige una tarea publicada" />
                      </SelectTrigger>
                      <SelectContent>
                        {banco.tareas.map((t) => (
                          <SelectItem key={t.id} value={String(t.id)}>
                            {t.asignatura} — {t.titulo} (entrega {formatoFecha.format(new Date(t.fecha_limite))})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                  {obligatoriosSinPreguntas.length > 0 && (
                    <p role="status" className="flex items-start gap-2 rounded-lg bg-warning/15 p-3 text-sm text-foreground">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                      {obligatoriosSinPreguntas.length} RA obligatorio(s) no quedan cubiertos por esta tarea.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 2b. Preguntas por RA (tipo cuestionario) */}
            {!esTarea && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">2. Preguntas por resultado de aprendizaje</CardTitle>
                <CardDescription>
                  {ef.preguntasElegidas.length} seleccionada(s). Solo aparecen preguntas aprobadas por los docentes
                  {banco.excluidas_por_laboratorio > 0 &&
                    `; ${banco.excluidas_por_laboratorio} se ocultaron por estar ya en el laboratorio de práctica`}
                  .
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {obligatoriosSinPreguntas.length > 0 && (
                  <p role="status" className="flex items-start gap-2 rounded-lg bg-warning/15 p-3 text-sm text-foreground">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                    {obligatoriosSinPreguntas.length} RA obligatorio(s) sin preguntas en esta evaluación.
                  </p>
                )}
                {banco.resultados.map((r) => {
                  const elegidas = r.preguntas.filter((p) => ef.preguntasElegidas.includes(p.id)).length
                  return (
                    <section key={r.resultado.id} className="space-y-2" aria-label={r.resultado.descripcion}>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-medium text-foreground">{r.resultado.descripcion}</h3>
                        <Badge variant="outline" className={r.obligatorio ? 'border-primary text-primary' : ''}>
                          {r.obligatorio ? 'Obligatorio' : 'Complementario'}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {elegidas} de {r.preguntas.length}
                        </span>
                      </div>
                      {r.preguntas.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          Sin preguntas aprobadas. El docente de la asignatura debe aprobarlas en su banco.
                        </p>
                      ) : (
                        <ul className="space-y-1.5">
                          {r.preguntas.map((p) => (
                            <li key={p.id}>
                              <label
                                className={cn(
                                  'flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm',
                                  ef.preguntasElegidas.includes(p.id) ? 'border-primary bg-primary/5' : 'border-border',
                                  ef.soloLectura && 'cursor-default',
                                )}
                              >
                                <input
                                  type="checkbox"
                                  className="mt-0.5 h-4 w-4 shrink-0 accent-primary"
                                  checked={ef.preguntasElegidas.includes(p.id)}
                                  disabled={ef.soloLectura}
                                  onChange={() => ef.alternarPregunta(p.id)}
                                />
                                <span className="min-w-0">
                                  <span className="block text-foreground">{p.enunciado}</span>
                                  <span className="block text-xs text-muted-foreground">
                                    {p.asignatura.codigo} · {p.opciones.length} opciones
                                    {p.competencia_transversal && ` · Transversal: ${p.competencia_transversal.nombre}`}
                                  </span>
                                </span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      )}
                    </section>
                  )
                })}
              </CardContent>
            </Card>

            )}

            {/* 3. Guardar / publicar */}
            {!ef.soloLectura && (
              <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <Button variant="outline" onClick={() => void ef.guardar()} disabled={ef.guardando || ef.publicando}>
                  {ef.guardando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Save className="mr-1.5 h-4 w-4" aria-hidden />}
                  Guardar borrador
                </Button>
                <Button
                  onClick={() => setConfirmarPublicar(true)}
                  disabled={typeof ef.seleccionadaId !== 'number' || !listaParaPublicar || ef.guardando}
                  title={typeof ef.seleccionadaId !== 'number' ? 'Guarda el borrador antes de publicar' : undefined}
                >
                  <Send className="mr-1.5 h-4 w-4" aria-hidden />
                  Publicar
                </Button>
              </div>
            )}

            {/* 4. Supervisión en sala, convocados y seguimiento (ADR-009) */}
            {ef.seleccionada && <PanelSupervision evaluacion={ef.seleccionada} alCambiar={ef.recargar} />}
          </div>
        )}
      </div>

      <Dialog open={confirmarPublicar} onOpenChange={setConfirmarPublicar}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Publicar evaluación</DialogTitle>
            <DialogDescription>
              Se guardarán los cambios y la evaluación quedará disponible en las fechas definidas. Después no
              podrás editar sus datos ni sus preguntas.
            </DialogDescription>
          </DialogHeader>
          {obligatoriosSinPreguntas.length > 0 && (
            <p className="text-sm text-foreground">
              Atención: {obligatoriosSinPreguntas.length} RA obligatorio(s) quedarán sin evaluar.
            </p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmarPublicar(false)} disabled={ef.publicando}>
              Cancelar
            </Button>
            <Button
              onClick={async () => {
                await ef.publicar()
                setConfirmarPublicar(false)
              }}
              disabled={ef.publicando || ef.guardando}
            >
              {(ef.publicando || ef.guardando) && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Publicar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
