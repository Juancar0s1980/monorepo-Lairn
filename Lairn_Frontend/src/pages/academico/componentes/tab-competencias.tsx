// Tab de Competencias + Resultados DCE con CRUD completo.

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import type { Academico } from '../use-academico'

export function TabCompetencias({ ac }: { ac: Academico }) {
  const transversales = ac.competencias.filter((c) => c.tipo === 'transversal').length
  const especificas = ac.competencias.filter((c) => c.tipo === 'especifica').length

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Competencias */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Competencias</CardTitle>
            <CardDescription>
              {transversales} transversales · {especificas} específicas
            </CardDescription>
          </div>
          <Button size="sm" onClick={ac.abrirCrearCompetencia} disabled={!ac.programaId}>
            <Plus className="h-4 w-4 mr-1.5" />
            Nueva
          </Button>
        </CardHeader>
        <CardContent>
          {ac.cargandoDetalle ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-3">
              {ac.competencias.map((c) => (
                <Card key={c.id} className="border-border bg-card">
                  <CardContent className="flex items-start justify-between gap-3 p-4">
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">{c.nombre}</p>
                      {c.descripcion && (
                        <p className="text-sm text-muted-foreground">{c.descripcion}</p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge
                        variant={c.tipo === 'transversal' ? 'secondary' : 'outline'}
                        className={
                          c.tipo === 'transversal'
                            ? 'bg-accent/20 text-accent-foreground border-transparent'
                            : ''
                        }
                      >
                        {c.tipo === 'transversal' ? 'Transversal' : 'Específica'}
                      </Badge>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => ac.abrirEditarCompetencia(c)}
                          title="Editar competencia"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            ac.setConfirmacion({ tipo: 'competencia', id: c.id, nombre: c.nombre })
                          }
                          title="Eliminar competencia"
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {!ac.competencias.length && (
                <p className="text-sm text-muted-foreground">Sin competencias todavía.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resultados de aprendizaje */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Resultados de aprendizaje (DCE)</CardTitle>
            <CardDescription>
              Afirmación → evidencia observable → tarea sugerida · {ac.resultados.length} RA
            </CardDescription>
          </div>
          <Button size="sm" onClick={ac.abrirCrearResultado} disabled={!ac.programaId}>
            <Plus className="h-4 w-4 mr-1.5" />
            Nuevo RA
          </Button>
        </CardHeader>
        <CardContent>
          {ac.cargandoDetalle ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-3">
              {ac.resultados.map((ra) => (
                <Card key={ra.id} className="border-border bg-card">
                  <CardContent className="space-y-2 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-foreground">{ra.descripcion}</p>
                      <div className="flex items-center gap-1">
                        <Badge variant="outline">v{ra.version}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => ac.abrirEditarResultado(ra)}
                          title="Editar RA"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            ac.setConfirmacion({
                              tipo: 'resultado',
                              id: ra.id,
                              nombre: ra.descripcion.slice(0, 60),
                            })
                          }
                          title="Eliminar RA"
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    {ra.evidencia_observable && (
                      <p className="text-xs text-muted-foreground">
                        <span className="font-semibold">Evidencia:</span> {ra.evidencia_observable}
                      </p>
                    )}
                    {ra.tarea_sugerida && (
                      <p className="text-xs text-muted-foreground">
                        <span className="font-semibold">Tarea:</span> {ra.tarea_sugerida}
                      </p>
                    )}
                    {ra.criterios_rubrica.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {ra.criterios_rubrica.map((c, i) => (
                          <Badge
                            key={i}
                            variant="secondary"
                            className="bg-secondary text-secondary-foreground border-transparent"
                          >
                            {c.criterio} {c.peso}%
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {!ac.resultados.length && (
                <p className="text-sm text-muted-foreground">
                  Sin resultados. Crea el primero vinculando competencia + asignatura.
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
