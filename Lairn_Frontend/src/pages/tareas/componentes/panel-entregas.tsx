// Panel de entregas de una tarea publicada (HU-08B.3) y calificación por
// niveles de rúbrica con nota calculada en vivo (HU-08B.4) y observaciones
// (HU-08B.5). Incluye a los inscritos que aún no entregan.
//
// HU-15: la IA puede proponer niveles, nota y observaciones. La propuesta es
// solo para el docente; nada se publica hasta "Aprobar y publicar".

import { useState } from 'react'
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
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { AlertTriangle, Download, EyeOff, Loader2, PenLine, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DecisionPreevaluacion, FilaEntrega, Preevaluacion, Tarea } from '@/types/tarea'
import type { TareasDocente } from '../use-tareas-docente'
import { ETIQUETA_ENTREGA, descargarArchivo, formatoFecha, notaPonderada } from '../utilidades-tareas'

const ETIQUETA_DECISION: Record<Exclude<DecisionPreevaluacion, 'pendiente'>, string> = {
  aprobada: 'Propuesta IA aprobada',
  ajustada: 'Propuesta IA ajustada',
}

function PropuestaIA({ propuesta, alUsar }: { propuesta: Preevaluacion; alUsar: () => void }) {
  return (
    <section
      aria-label="Propuesta de la IA"
      className="space-y-2 rounded-xl border border-primary/30 bg-primary/5 p-3 text-sm"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 font-medium">
          <Sparkles className="h-4 w-4 text-primary" aria-hidden />
          Propuesta de la IA: <span className="text-primary">{propuesta.nota_propuesta}</span>
          <span className="font-normal text-muted-foreground">/ 5.00</span>
        </p>
        <Button variant="outline" size="sm" onClick={alUsar}>
          Usar propuesta
        </Button>
      </div>
      <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
        <EyeOff className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
        Solo tú la ves. Es un apoyo: revisa la entrega, ajusta lo que haga falta y aprueba para publicar la nota.
      </p>
      {propuesta.advertencias.map((a) => (
        <p key={a} className="flex items-start gap-1.5 text-xs text-warning">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          {a}
        </p>
      ))}
    </section>
  )
}

function FormularioCalificacion({ fila, tarea, td }: { fila: FilaEntrega; tarea: Tarea; td: TareasDocente }) {
  const previa = fila.entrega?.calificacion
  const propuesta = fila.entrega?.preevaluacion ?? null
  // Sin nota previa, se parte de la propuesta de la IA (si existe) para que el docente la revise.
  const inicialIA = !previa && propuesta
  const [niveles, setNiveles] = useState<(number | null)[]>(
    previa ? previa.niveles_elegidos : inicialIA ? propuesta.niveles_propuestos : tarea.rubrica.map(() => null),
  )
  const [observaciones, setObservaciones] = useState(
    previa?.observaciones ?? (inicialIA ? propuesta.observaciones_propuestas : ''),
  )
  const nota = notaPonderada(tarea.rubrica, niveles)
  const analizando = !!fila.entrega && td.analizando.includes(fila.entrega.id)
  const aprobando = !!propuesta && !previa

  const usarPropuesta = () => {
    if (!propuesta) return
    setNiveles(propuesta.niveles_propuestos)
    setObservaciones(propuesta.observaciones_propuestas)
  }

  return (
    <>
      <div className="max-h-[65vh] space-y-4 overflow-y-auto pr-1">
        {propuesta && !previa ? (
          <PropuestaIA propuesta={propuesta} alUsar={usarPropuesta} />
        ) : (
          !previa && fila.entrega && (
            <Button
              variant="outline"
              size="sm"
              disabled={analizando}
              onClick={() => fila.entrega && void td.preevaluar(fila.entrega.id)}
            >
              {analizando ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Sparkles className="mr-1.5 h-4 w-4" aria-hidden />
              )}
              {analizando ? 'Analizando la entrega…' : 'Analizar con IA'}
            </Button>
          )
        )}
        {tarea.rubrica.map((c, i) => {
          const sugerido = propuesta && !previa ? propuesta.analisis[i] : undefined
          return (
            <fieldset key={i} className="space-y-1.5">
              <legend className="text-sm font-medium">
                {c.criterio} <span className="font-normal text-muted-foreground">({c.peso} %)</span>
              </legend>
              <div className="flex flex-wrap gap-2">
                {c.niveles.map((n, k) => (
                  <button
                    key={k}
                    type="button"
                    aria-pressed={niveles[i] === k}
                    onClick={() => setNiveles((actual) => actual.map((x, j) => (j === i ? k : x)))}
                    className={cn(
                      'rounded-lg border px-3 py-1.5 text-sm transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                      niveles[i] === k ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-muted',
                    )}
                  >
                    {n.nombre} · {n.valor}
                    {sugerido?.nivel === k && (
                      <Sparkles className="ml-1 inline h-3 w-3" aria-label="sugerido por la IA" />
                    )}
                  </button>
                ))}
              </div>
              {sugerido?.justificacion && (
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">IA:</span> {sugerido.justificacion}
                </p>
              )}
            </fieldset>
          )
        })}
        <div className="space-y-1.5">
          <Label htmlFor="observaciones">Observaciones para el estudiante</Label>
          <Textarea id="observaciones" value={observaciones} onChange={(e) => setObservaciones(e.target.value)} />
        </div>
        <p className="text-sm" aria-live="polite">
          Nota calculada: <span className="text-lg font-bold text-primary">{nota === null ? '—' : nota.toFixed(2)}</span>
          <span className="text-muted-foreground"> / 5.00</span>
        </p>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => td.setCalificando(null)} disabled={td.guardandoNota}>
          Cancelar
        </Button>
        <Button
          disabled={nota === null || td.guardandoNota || !fila.entrega}
          onClick={() => fila.entrega && void td.calificar(fila.entrega.id, niveles as number[], observaciones)}
        >
          {td.guardandoNota && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
          {aprobando ? 'Aprobar y publicar' : 'Guardar calificación'}
        </Button>
      </DialogFooter>
    </>
  )
}

function CeldaNota({ fila }: { fila: FilaEntrega }) {
  const e = fila.entrega
  if (e?.calificacion) {
    const decision = e.preevaluacion?.decision
    return (
      <span className="font-medium">
        {e.calificacion.nota}
        {decision && decision !== 'pendiente' && (
          <span className="block text-xs font-normal text-muted-foreground">{ETIQUETA_DECISION[decision]}</span>
        )}
      </span>
    )
  }
  if (e?.preevaluacion) {
    return (
      <span className="text-sm text-muted-foreground">
        <Sparkles className="mr-1 inline h-3.5 w-3.5 text-primary" aria-hidden />
        {e.preevaluacion.nota_propuesta}
        <span className="block text-xs">Propuesta IA · sin publicar</span>
      </span>
    )
  }
  return <span className="font-medium">—</span>
}

export function PanelEntregas({ td, tarea }: { td: TareasDocente; tarea: Tarea }) {
  const entregadas = td.entregas.filter((f) => f.entrega).length
  const pendientesIA = td.entregas.filter((f) => f.entrega && !f.entrega.calificacion && !f.entrega.preevaluacion).length
  const enLote = td.progresoIA !== null
  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="space-y-1.5">
          <CardTitle className="text-base">Entregas</CardTitle>
          <CardDescription>
            {entregadas} de {td.entregas.length} estudiantes · fecha límite {formatoFecha.format(new Date(tarea.fecha_limite))}
          </CardDescription>
        </div>
        {(pendientesIA > 0 || enLote) && (
          <Button variant="outline" size="sm" disabled={enLote || td.analizando.length > 0} onClick={() => void td.preevaluarPendientes()}>
            {enLote ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Sparkles className="mr-1.5 h-4 w-4" aria-hidden />
            )}
            {enLote
              ? `Analizando ${td.progresoIA!.hechas} de ${td.progresoIA!.total}…`
              : `Analizar ${pendientesIA} pendiente(s) con IA`}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {td.entregas.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No hay estudiantes inscritos en el curso vinculado a esta asignatura.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Estudiante</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="hidden md:table-cell">Enviada</TableHead>
                <TableHead>Nota</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {td.entregas.map((f) => {
                const analizando = !!f.entrega && td.analizando.includes(f.entrega.id)
                return (
                  <TableRow key={f.estudiante.id}>
                    <TableCell>
                      <span className="block font-medium">{f.estudiante.nombre}</span>
                      <span className="block text-xs text-muted-foreground">{f.estudiante.email}</span>
                    </TableCell>
                    <TableCell>
                      <Badge className={cn('border-transparent', ETIQUETA_ENTREGA[f.estado].clase)}>
                        {ETIQUETA_ENTREGA[f.estado].texto}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden text-xs text-muted-foreground md:table-cell">
                      {f.entrega ? formatoFecha.format(new Date(f.entrega.enviada_en)) : '—'}
                    </TableCell>
                    <TableCell>
                      {analizando ? (
                        <span className="text-xs text-muted-foreground">
                          <Loader2 className="mr-1 inline h-3.5 w-3.5 animate-spin" aria-hidden />
                          Analizando…
                        </span>
                      ) : (
                        <CeldaNota fila={f} />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {f.entrega && (
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            aria-label={`Descargar entrega de ${f.estudiante.nombre}`}
                            onClick={() =>
                              f.entrega && void descargarArchivo(`/evaluacion/docente/entregas/${f.entrega.id}/archivo/`, f.entrega.nombre)
                            }
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          {!f.entrega.calificacion && !f.entrega.preevaluacion && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              aria-label={`Analizar con IA la entrega de ${f.estudiante.nombre}`}
                              title="Analizar con IA"
                              disabled={analizando || enLote}
                              onClick={() => f.entrega && void td.preevaluar(f.entrega.id)}
                            >
                              <Sparkles className="h-4 w-4" />
                            </Button>
                          )}
                          <Button variant="outline" size="sm" onClick={() => td.setCalificando(f)}>
                            <PenLine className="mr-1 h-3.5 w-3.5" aria-hidden />
                            {f.entrega.calificacion
                              ? 'Editar nota'
                              : f.entrega.preevaluacion
                                ? 'Revisar propuesta'
                                : 'Calificar'}
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>

      <Dialog open={!!td.calificando} onOpenChange={(v) => !v && td.setCalificando(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Calificar entrega</DialogTitle>
            <DialogDescription>
              {td.calificando?.estudiante.nombre} · elige el nivel alcanzado en cada criterio.
            </DialogDescription>
          </DialogHeader>
          {td.calificando && (
            <FormularioCalificacion
              key={`${td.calificando.estudiante.id}-${td.calificando.entrega?.preevaluacion?.generada_en ?? ''}`}
              fila={td.calificando}
              tarea={tarea}
              td={td}
            />
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}
