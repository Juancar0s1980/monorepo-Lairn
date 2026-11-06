// Tab de Programas: tabla con buscar, crear, editar y desactivar.
// Usa solo Shadcn/UI + paleta de src/index.css.

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { CircleOff, Pencil, Plus, Search } from 'lucide-react'
import { BadgeRevision, etiquetaOrigen } from '../academico-utils'
import type { Academico } from '../use-academico'

export function TabProgramas({ ac }: { ac: Academico }) {
  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 space-y-0 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>Programas académicos</CardTitle>
          <CardDescription>
            {ac.programasFiltrados.length} de {ac.programas.length} programas ·{' '}
            {ac.esAdmin
              ? 'crea, edita o desactiva programas'
              : 'consulta de la oferta académica vigente'}
          </CardDescription>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar..."
              value={ac.busqueda}
              onChange={(e) => ac.setBusqueda(e.target.value)}
              aria-label="Buscar programa por nombre o código"
              className="w-full pl-8 sm:w-[200px]"
            />
          </div>
          {/* Crear/editar programas es exclusivo del Administrador (HU-01.1 / 01.2) */}
          {ac.esAdmin && (
            <Button onClick={ac.abrirCrearPrograma}>
              <Plus className="h-4 w-4 mr-1.5" />
              Nuevo programa
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {ac.programasFiltrados.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Sin programas. Crea el primero con “Nuevo programa”.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código</TableHead>
                <TableHead>Programa</TableHead>
                <TableHead>Modalidad</TableHead>
                <TableHead>Sede</TableHead>
                <TableHead className="text-right">Duración</TableHead>
                <TableHead>Origen</TableHead>
                <TableHead>Estado</TableHead>
                {ac.esAdmin && <TableHead className="text-right">Acciones</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {ac.programasFiltrados.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono text-xs">{p.codigo}</TableCell>
                  <TableCell className="font-medium">{p.nombre}</TableCell>
                  <TableCell>{p.modalidad}</TableCell>
                  <TableCell>{p.sede}</TableCell>
                  <TableCell className="text-right">{p.duracion_semestres} sem.</TableCell>
                  <TableCell>
                    <Badge variant="outline">{etiquetaOrigen(p.origen)}</Badge>
                  </TableCell>
                  <TableCell>
                    <BadgeRevision estado={p.estado_revision} />
                  </TableCell>
                  {ac.esAdmin && (
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => ac.abrirEditarPrograma(p)}
                        title="Editar programa"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          ac.setConfirmacion({ tipo: 'programa', id: p.id, nombre: p.nombre })
                        }
                        title="Desactivar programa (borrado lógico)"
                      >
                        <CircleOff className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
