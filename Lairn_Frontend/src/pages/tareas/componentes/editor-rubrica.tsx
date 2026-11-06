// Editor de rúbrica (HU-08B.2): criterios con peso y niveles con valor 0-5.
// Muestra la suma de pesos y alerta si no es 100 % (el backend también lo
// valida y no deja publicar).

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AlertTriangle, Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CriterioRubrica } from '@/types/tarea'

const MAX_CRITERIOS = 10
const MAX_NIVELES = 5
const MIN_NIVELES = 2

export function EditorRubrica({
  rubrica,
  alCambiar,
  deshabilitado,
}: {
  rubrica: CriterioRubrica[]
  alCambiar: (r: CriterioRubrica[]) => void
  deshabilitado?: boolean
}) {
  const suma = rubrica.reduce((s, c) => s + (Number(c.peso) || 0), 0)
  const cambiarCriterio = (i: number, cambios: Partial<CriterioRubrica>) =>
    alCambiar(rubrica.map((c, j) => (j === i ? { ...c, ...cambios } : c)))
  const cambiarNivel = (i: number, k: number, cambios: Partial<CriterioRubrica['niveles'][number]>) =>
    cambiarCriterio(i, { niveles: rubrica[i].niveles.map((n, m) => (m === k ? { ...n, ...cambios } : n)) })

  return (
    <div className="space-y-3">
      <p
        role="status"
        className={cn(
          'flex items-center gap-2 text-sm',
          suma === 100 ? 'text-muted-foreground' : 'font-medium text-destructive',
        )}
      >
        {suma !== 100 && <AlertTriangle className="h-4 w-4" aria-hidden />}
        Los pesos suman {suma} %{suma !== 100 && ': deben sumar exactamente 100 %'}
      </p>
      {rubrica.map((c, i) => (
        <fieldset key={i} disabled={deshabilitado} className="space-y-2 rounded-lg border border-border p-3">
          <legend className="sr-only">Criterio {i + 1}</legend>
          <div className="grid gap-2 sm:grid-cols-[1fr_110px_auto]">
            <Input
              aria-label={`Nombre del criterio ${i + 1}`}
              placeholder="Criterio (p. ej. Análisis del caso)"
              value={c.criterio}
              onChange={(e) => cambiarCriterio(i, { criterio: e.target.value })}
            />
            <div className="flex items-center gap-1">
              <Input
                type="number"
                min={1}
                max={100}
                aria-label={`Peso del criterio ${i + 1} en porcentaje`}
                value={c.peso}
                onChange={(e) => cambiarCriterio(i, { peso: Number(e.target.value) })}
              />
              <span className="text-sm text-muted-foreground">%</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => alCambiar(rubrica.filter((_, j) => j !== i))}
              disabled={rubrica.length <= 1}
              aria-label={`Quitar el criterio ${i + 1}`}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
          <div className="space-y-1.5 pl-0 sm:pl-3">
            {c.niveles.map((n, k) => (
              <div key={k} className="grid grid-cols-[1fr_80px_auto] items-center gap-2">
                <Input
                  aria-label={`Nivel ${k + 1} del criterio ${i + 1}`}
                  placeholder="Nivel (p. ej. Básico)"
                  value={n.nombre}
                  onChange={(e) => cambiarNivel(i, k, { nombre: e.target.value })}
                />
                <Input
                  type="number"
                  min={0}
                  max={5}
                  step={0.1}
                  aria-label={`Valor del nivel ${k + 1} (0 a 5)`}
                  value={n.valor}
                  onChange={(e) => cambiarNivel(i, k, { valor: Number(e.target.value) })}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => cambiarCriterio(i, { niveles: c.niveles.filter((_, m) => m !== k) })}
                  disabled={c.niveles.length <= MIN_NIVELES}
                  aria-label={`Quitar el nivel ${k + 1}`}
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}
            {c.niveles.length < MAX_NIVELES && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => cambiarCriterio(i, { niveles: [...c.niveles, { nombre: '', descripcion: '', valor: 5 }] })}
              >
                <Plus className="mr-1 h-3.5 w-3.5" aria-hidden />
                Nivel
              </Button>
            )}
          </div>
        </fieldset>
      ))}
      {!deshabilitado && rubrica.length < MAX_CRITERIOS && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            alCambiar([
              ...rubrica,
              {
                criterio: '',
                descripcion: '',
                peso: Math.max(0, 100 - suma),
                niveles: [
                  { nombre: 'Bajo', descripcion: '', valor: 1 },
                  { nombre: 'Alto', descripcion: '', valor: 5 },
                ],
              },
            ])
          }
        >
          <Plus className="mr-1.5 h-4 w-4" aria-hidden />
          Agregar criterio
        </Button>
      )}
    </div>
  )
}
