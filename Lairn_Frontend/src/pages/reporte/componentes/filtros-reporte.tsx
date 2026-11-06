// Filtros globales del reporte institucional (ADR-011): programa, semestre,
// momento, rango de fechas, asignatura, docente y competencia. Todos los
// gráficos, tablas, mapas y exportaciones responden a ellos. Viven en la URL.

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ChevronDown, Filter, FilterX } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ClaveFiltro, FiltroReporte, OpcionesReporte } from '@/types/reporte'

const TODOS = 'todos'

// Al cambiar un filtro, se limpian los que dependen de él.
const DEPENDIENTES: Partial<Record<ClaveFiltro, ClaveFiltro[]>> = {
  programa: ['semestre', 'momento', 'asignatura', 'docente', 'competencia', 'resultado', 'evaluacion'],
  semestre: ['asignatura', 'resultado', 'evaluacion'],
  asignatura: ['resultado', 'evaluacion'],
  momento: ['evaluacion'],
}

function Selector({
  id,
  etiqueta,
  valor,
  opciones,
  alCambiar,
}: {
  id: ClaveFiltro
  etiqueta: string
  valor: string | undefined
  opciones: { id: number; nombre: string }[]
  alCambiar: (clave: ClaveFiltro, valor: string | undefined) => void
}) {
  const items = [{ value: TODOS, label: 'Todos' }, ...opciones.map((o) => ({ value: String(o.id), label: o.nombre }))]
  return (
    <div className="min-w-0 space-y-1">
      <Label htmlFor={`filtro-${id}`} className="text-xs text-muted-foreground">
        {etiqueta}
      </Label>
      <Select
        value={valor ?? TODOS}
        onValueChange={(v) => alCambiar(id, !v || v === TODOS ? undefined : v)}
        items={items}
      >
        <SelectTrigger id={`filtro-${id}`} className="w-full min-w-0">
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
    </div>
  )
}

export function FiltrosReporte({
  filtros,
  opciones,
  alCambiar,
}: {
  filtros: FiltroReporte
  opciones: OpcionesReporte | null
  alCambiar: (nuevos: FiltroReporte) => void
}) {
  const cambiar = (clave: ClaveFiltro, valor: string | undefined) => {
    const nuevos: FiltroReporte = { ...filtros, [clave]: valor }
    for (const dep of DEPENDIENTES[clave] ?? []) delete nuevos[dep]
    if (valor === undefined) delete nuevos[clave]
    alCambiar(nuevos)
  }
  const v = (clave: ClaveFiltro) => (filtros[clave] === undefined ? undefined : String(filtros[clave]))
  const hayFiltros = Object.keys(filtros).length > 0
  // En móvil los filtros se pliegan para no empujar el tablero hacia abajo.
  const [abierto, setAbierto] = useState(false)

  return (
    <Card>
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
        className="flex w-full items-center justify-between p-4 text-sm font-medium text-foreground sm:hidden"
      >
        <span className="flex items-center gap-2">
          <Filter className="h-4 w-4" aria-hidden />
          Filtros{hayFiltros && ` (${Object.keys(filtros).length} activos)`}
        </span>
        <ChevronDown className={cn('h-4 w-4 transition-transform', abierto && 'rotate-180')} aria-hidden />
      </button>
      <CardContent
        className={cn(
          'grid-cols-1 gap-3 p-4 pt-0 sm:grid sm:grid-cols-2 sm:pt-4 lg:grid-cols-4 xl:grid-cols-8',
          abierto ? 'grid' : 'hidden',
        )}
      >
        <Selector id="programa" etiqueta="Programa" valor={v('programa')} opciones={opciones?.programas ?? []} alCambiar={cambiar} />
        <Selector id="semestre" etiqueta="Semestre" valor={v('semestre')} opciones={opciones?.semestres ?? []} alCambiar={cambiar} />
        <Selector id="momento" etiqueta="Momento" valor={v('momento')} opciones={opciones?.momentos ?? []} alCambiar={cambiar} />
        <Selector id="asignatura" etiqueta="Asignatura" valor={v('asignatura')} opciones={opciones?.asignaturas ?? []} alCambiar={cambiar} />
        <Selector id="docente" etiqueta="Docente" valor={v('docente')} opciones={opciones?.docentes ?? []} alCambiar={cambiar} />
        <Selector id="competencia" etiqueta="Competencia" valor={v('competencia')} opciones={opciones?.competencias ?? []} alCambiar={cambiar} />
        <div className="min-w-0 space-y-1">
          <Label htmlFor="filtro-desde" className="text-xs text-muted-foreground">Desde</Label>
          <Input id="filtro-desde" type="date" value={v('desde') ?? ''} max={v('hasta')} onChange={(e) => cambiar('desde', e.target.value || undefined)} />
        </div>
        <div className="min-w-0 space-y-1">
          <Label htmlFor="filtro-hasta" className="text-xs text-muted-foreground">Hasta</Label>
          <Input id="filtro-hasta" type="date" value={v('hasta') ?? ''} min={v('desde')} onChange={(e) => cambiar('hasta', e.target.value || undefined)} />
        </div>
        {hayFiltros && (
          <div className="sm:col-span-2 lg:col-span-4 xl:col-span-8">
            <Button variant="ghost" size="sm" onClick={() => alCambiar({})}>
              <FilterX className="mr-1.5 h-4 w-4" aria-hidden />
              Quitar todos los filtros
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
