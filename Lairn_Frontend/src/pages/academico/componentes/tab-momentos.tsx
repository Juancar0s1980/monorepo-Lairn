// Tab de Momentos: CRUD + vínculos a RA + tablero resumido.

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Link2, Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import type { Academico } from '../use-academico'

export function TabMomentos({ ac }: { ac: Academico }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Momentos de evaluación</CardTitle>
          <CardDescription>
            Dependen de cada carrera (ej. Ing. Software: 4-6-8) · {ac.momentos.length} momentos
          </CardDescription>
        </div>
        <Button size="sm" onClick={ac.abrirCrearMomento} disabled={!ac.programaId}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nuevo momento
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
                <TableHead>Momento</TableHead>
                <TableHead>Semestre</TableHead>
                <TableHead>Periodo</TableHead>
                <TableHead className="text-right">RAs</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ac.momentos.map((m) => (
                <TableRow key={m.id}>
                  <TableCell className="font-medium">{m.nombre}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="bg-primary/10 text-primary border-transparent">
                      Semestre {m.semestre_referencia}
                    </Badge>
                  </TableCell>
                  <TableCell>{m.periodo || '—'}</TableCell>
                  <TableCell className="text-right">{m.total_ras}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => ac.abrirVinculos(m)}
                        title="Vincular resultados"
                      >
                        <Link2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => ac.abrirEditarMomento(m)}
                        title="Editar momento"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          ac.setConfirmacion({ tipo: 'momento', id: m.id, nombre: m.nombre })
                        }
                        title="Eliminar momento"
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
        {!ac.cargandoDetalle && !ac.momentos.length && (
          <p className="pt-3 text-sm text-muted-foreground">
            Sin momentos definidos para este programa.
          </p>
        )}
        {/* Detalle del tablero (RAs por momento) */}
        <div className="mt-4 space-y-3">
          {ac.tablero?.momentos.map((m) => (
            <Card key={m.momento_id} className="border-border bg-card">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{m.nombre}</CardTitle>
                  <Badge variant="secondary" className="bg-primary/10 text-primary border-transparent">
                    Semestre {m.semestre}
                  </Badge>
                </div>
                <CardDescription>
                  {m.total_ras} resultado(s) de aprendizaje vinculado(s)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Resultado de aprendizaje</TableHead>
                      <TableHead className="w-[100px]">Obligatorio</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {m.ras.map((ra) => (
                      <TableRow key={ra.id}>
                        <TableCell className="text-sm">{ra.descripcion}</TableCell>
                        <TableCell>
                          {ra.obligatorio ? (
                            <Badge className="bg-success/10 text-success border-transparent">
                              Sí
                            </Badge>
                          ) : (
                            <Badge variant="outline">No</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
