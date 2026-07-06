// Tab de estudiantes para el docente.
//
// Muestra una tabla simplificada con los estudiantes inscritos en el curso.
// Permite eliminar estudiantes con diálogo de confirmación.

import { useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Loader2, Users, Trash2, Mail } from 'lucide-react'
import { toast } from 'sonner'
import type { ResumenCursoDocente } from '@/types/analitica'

interface TabEstudiantesDocenteProps {
  resumen: ResumenCursoDocente | null
  cargandoResumen: boolean
  cursoId: string
  onEstudianteEliminado: (estudianteId: number) => void
}

export function TabEstudiantesDocente({
  resumen,
  cargandoResumen,
  cursoId,
  onEstudianteEliminado,
}: TabEstudiantesDocenteProps) {
  const [estudianteAEliminar, setEstudianteAEliminar] = useState<{
    id: number
    nombre: string
  } | null>(null)
  const [eliminando, setEliminando] = useState(false)

  // Elimina un estudiante del curso.
  const eliminarEstudiante = async () => {
    if (!estudianteAEliminar) return
    setEliminando(true)
    try {
      await api.delete(
        `/examenes/cursos/${cursoId}/estudiantes/${estudianteAEliminar.id}/`
      )
      toast.success('Estudiante eliminado del curso')
      onEstudianteEliminado(estudianteAEliminar.id)
      setEstudianteAEliminar(null)
    } catch {
      toast.error('No se pudo eliminar el estudiante')
    } finally {
      setEliminando(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Estado de carga de estudiantes */}
      {cargandoResumen && (
        <div className="flex h-[40vh] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Estado vacío de estudiantes */}
      {!cargandoResumen &&
        (!resumen || resumen.estudiantes.length === 0) && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <Users className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              No hay estudiantes en este curso
            </p>
            <p className="text-xs text-muted-foreground/70">
              Los estudiantes aparecerán aquí cuando se inscriban
            </p>
          </div>
        )}

      {/* Tabla simplificada de estudiantes */}
      {!cargandoResumen &&
        resumen &&
        resumen.estudiantes.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Estudiante</TableHead>
                <TableHead className="hidden sm:table-cell">
                  Email
                </TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {resumen.estudiantes.map((est) => (
                <TableRow key={est.estudiante_id}>
                  <TableCell>
                    <p className="font-medium">{est.nombre}</p>
                    <p className="text-xs text-muted-foreground sm:hidden flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {est.email}
                    </p>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5" />
                      {est.email}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() =>
                        setEstudianteAEliminar({
                          id: est.estudiante_id,
                          nombre: est.nombre,
                        })
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

      {/* Diálogo de confirmación para eliminar estudiante */}
      <Dialog
        open={!!estudianteAEliminar}
        onOpenChange={(open) => !open && setEstudianteAEliminar(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Eliminar Estudiante</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que deseas eliminar a{' '}
              <span className="font-medium text-foreground">
                {estudianteAEliminar?.nombre}
              </span>{' '}
              del curso? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEstudianteAEliminar(null)}
              disabled={eliminando}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={eliminarEstudiante}
              disabled={eliminando}
            >
              {eliminando ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Eliminando...
                </div>
              ) : (
                'Eliminar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
