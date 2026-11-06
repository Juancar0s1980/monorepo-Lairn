// Panel de entregas de una tarea publicada (HU-08B.3) y calificación por
// niveles de rúbrica con nota calculada en vivo (HU-08B.4) y observaciones
// (HU-08B.5). Incluye a los inscritos que aún no entregan.

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
import { Download, Loader2, PenLine } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FilaEntrega, Tarea } from '@/types/tarea'
import type { TareasDocente } from '../use-tareas-docente'
import { ETIQUETA_ENTREGA, descargarArchivo, formatoFecha, notaPonderada } from '../utilidades-tareas'

function FormularioCalificacion({ fila, tarea, td }: { fila: FilaEntrega; tarea: Tarea; td: TareasDocente }) {
  const previa = fila.entrega?.calificacion
  const [niveles, setNiveles] = useState<(number | null)[]>(
    previa ? previa.niveles_elegidos : tarea.rubrica.map(() => null),
  )
  const [observaciones, setObservaciones] = useState(previa?.observaciones ?? '')
  const nota = notaPonderada(tarea.rubrica, niveles)

  return (
    <>
      <div className="space-y-4">
        {tarea.rubrica.map((c, i) => (
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
                </button>
              ))}
            </div>
          </fieldset>
        ))}
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
          Guardar calificación
        </Button>
      </DialogFooter>
    </>
  )
}

export function PanelEntregas({ td, tarea }: { td: TareasDocente; tarea: Tarea }) {
  const entregadas = td.entregas.filter((f) => f.entrega).length
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Entregas</CardTitle>
        <CardDescription>
          {entregadas} de {td.entregas.length} estudiantes · fecha límite {formatoFecha.format(new Date(tarea.fecha_limite))}
        </CardDescription>
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
              {td.entregas.map((f) => (
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
                  <TableCell className="font-medium">{f.entrega?.calificacion?.nota ?? '—'}</TableCell>
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
                        <Button variant="outline" size="sm" onClick={() => td.setCalificando(f)}>
                          <PenLine className="mr-1 h-3.5 w-3.5" aria-hidden />
                          {f.entrega.calificacion ? 'Editar nota' : 'Calificar'}
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
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
            <FormularioCalificacion key={td.calificando.estudiante.id} fila={td.calificando} tarea={tarea} td={td} />
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}
