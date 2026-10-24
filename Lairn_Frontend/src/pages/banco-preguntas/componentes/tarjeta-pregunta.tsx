// Tarjeta de una pregunta del banco para la curaduría docente.
// Muestra el caso, el enunciado, las opciones con la correcta marcada, la
// justificación y su categorización (RA y competencia transversal, HU-04.3).
// Las acciones solo aparecen mientras la pregunta está pendiente (HU-05.2-05.4).

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Check, CheckCircle2, Loader2, Pencil, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { PreguntaBanco } from '@/types/banco'
import type { BancoPreguntas } from '../use-banco-preguntas'

const LETRAS = ['A', 'B', 'C', 'D', 'E', 'F']

export function TarjetaPregunta({ p, bp }: { p: PreguntaBanco; bp: BancoPreguntas }) {
  const ocupada = bp.procesandoId === p.id
  return (
    <Card>
      <CardContent className="space-y-4 p-4 sm:p-5">
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline" className="max-w-full whitespace-normal text-left">
            RA: {p.resultado.descripcion}
          </Badge>
          {p.competencia_transversal ? (
            <Badge className="border-transparent bg-accent text-accent-foreground">
              Transversal: {p.competencia_transversal.nombre}
            </Badge>
          ) : (
            <Badge variant="outline" className="text-muted-foreground">Sin competencia transversal</Badge>
          )}
        </div>

        {p.contexto && (
          <div className="rounded-lg bg-muted p-3 text-sm text-foreground">
            <p className="mb-1 text-xs font-medium text-muted-foreground">Caso</p>
            <p className="whitespace-pre-line">{p.contexto}</p>
          </div>
        )}
        <p className="font-medium text-foreground whitespace-pre-line">{p.enunciado}</p>

        <ol className="space-y-1.5" aria-label="Opciones de respuesta">
          {p.opciones.map((opcion, i) => {
            const correcta = i === p.respuesta_correcta
            return (
              <li
                key={i}
                className={cn(
                  'flex items-start gap-2 rounded-lg border p-2 text-sm',
                  correcta ? 'border-success/50 bg-success/10' : 'border-border',
                )}
              >
                <span className="font-mono text-xs text-muted-foreground">{LETRAS[i]}.</span>
                <span className="flex-1">{opcion}</span>
                {correcta && (
                  <span className="flex items-center gap-1 text-xs font-medium text-success">
                    <Check className="h-3.5 w-3.5" aria-hidden />
                    Correcta
                  </span>
                )}
              </li>
            )
          })}
        </ol>

        {p.retroalimentacion && (
          <details className="text-sm">
            <summary className="cursor-pointer text-xs font-medium text-primary">Ver justificación</summary>
            <p className="mt-2 whitespace-pre-line text-muted-foreground">{p.retroalimentacion}</p>
          </details>
        )}

        {p.estado === 'descartada' && p.motivo_descarte && (
          <p className="text-xs text-muted-foreground">Motivo del descarte: {p.motivo_descarte}</p>
        )}

        {p.estado === 'pendiente' && (
          <div className="flex flex-col-reverse gap-2 border-t border-border pt-3 sm:flex-row sm:justify-end">
            <Button variant="ghost" onClick={() => bp.setDescartando(p)} disabled={ocupada}>
              <XCircle className="mr-1.5 h-4 w-4 text-destructive" aria-hidden />
              Descartar
            </Button>
            <Button variant="outline" onClick={() => bp.setEditando(p)} disabled={ocupada}>
              <Pencil className="mr-1.5 h-4 w-4" aria-hidden />
              Editar
            </Button>
            <Button onClick={() => bp.aprobar(p.id)} disabled={ocupada}>
              {ocupada ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <CheckCircle2 className="mr-1.5 h-4 w-4" aria-hidden />
              )}
              Aprobar
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
