// Tab de Malla: semestres + asignaturas con CRUD completo.
// Muestra el número de semestre legible (semestre_numero del backend).

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { etiquetaOrigen } from '../academico-utils'
import type { Academico } from '../use-academico'

export function TabMalla({ ac }: { ac: Academico }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Semestres */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Semestres del programa</CardTitle>
            <CardDescription>{ac.semestres.length} semestres en la malla</CardDescription>
          </div>
          <Button size="sm" onClick={ac.abrirCrearSemestre} disabled={!ac.programaId}>
            <Plus className="h-4 w-4 mr-1.5" />
            Nuevo
          </Button>
        </CardHeader>
        <CardContent>
          {ac.cargandoDetalle ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">N.º</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Origen</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ac.semestres.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono">{s.numero}</TableCell>
                    <TableCell>{s.nombre || `Semestre ${s.numero}`}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{etiquetaOrigen(s.origen)}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => ac.abrirEditarSemestre(s)}
                          title="Editar semestre"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            ac.setConfirmacion({
                              tipo: 'semestre',
                              id: s.id,
                              nombre: `Semestre ${s.numero}`,
                            })
                          }
                          title="Eliminar semestre"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {!ac.cargandoDetalle && !ac.semestres.length && (
            <p className="pt-3 text-sm text-muted-foreground">
              Sin semestres. Crea el primero para ubicar asignaturas.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Asignaturas */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Asignaturas</CardTitle>
            <CardDescription>{ac.asignaturas.length} en el catálogo del programa</CardDescription>
          </div>
          <Button size="sm" onClick={ac.abrirCrearAsignatura} disabled={!ac.programaId}>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Código</TableHead>
                  <TableHead>Asignatura</TableHead>
                  <TableHead className="text-right">Créd.</TableHead>
                  <TableHead>Sem.</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ac.asignaturas.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-mono text-xs">{a.codigo}</TableCell>
                    <TableCell className="font-medium">
                      {a.nombre}
                      <span className="block text-[11px] font-normal capitalize text-muted-foreground">
                        {a.tipo} · {a.intensidad_horaria}h
                      </span>
                    </TableCell>
                    <TableCell className="text-right">{a.creditos}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{ac.nombreSemestre(a)}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => ac.abrirEditarAsignatura(a)}
                          title="Editar asignatura"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            ac.setConfirmacion({ tipo: 'asignatura', id: a.id, nombre: a.nombre })
                          }
                          title="Eliminar asignatura"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {!ac.cargandoDetalle && !ac.asignaturas.length && (
            <p className="pt-3 text-sm text-muted-foreground">
              Sin asignaturas. Crea la primera del programa.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
