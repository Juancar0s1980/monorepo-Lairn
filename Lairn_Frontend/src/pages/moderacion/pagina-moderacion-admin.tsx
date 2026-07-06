// Moderación de cursos y exámenes reportados (solo accesible para Administrador).
// Lista los reportes creados por docentes o estudiantes sobre contenido
// problemático y permite marcarlos como resueltos, descartarlos o reabrirlos.
// Obtiene los datos de GET /moderacion/reportes/ y actualiza con
// PATCH /moderacion/reportes/<id>/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { BookOpen, Check, FileText, Flag, RotateCcw, X } from 'lucide-react'
import { toast } from 'sonner'

type EstadoReporte = 'pendiente' | 'resuelto' | 'descartado'

interface ReporteAdmin {
  id: number
  motivo: string
  estado: EstadoReporte
  creado_en: string
  resuelto_en: string | null
  reportado_por: string
  curso: number | null
  curso_nombre: string | null
  examen: number | null
  examen_titulo: string | null
}

const filtros: Array<{ value: string; label: string }> = [
  { value: 'pendiente', label: 'Pendientes' },
  { value: 'resuelto', label: 'Resueltos' },
  { value: 'descartado', label: 'Descartados' },
  { value: 'todos', label: 'Todos' },
]

const estiloEstado: Record<EstadoReporte, 'default' | 'secondary' | 'destructive'> = {
  pendiente: 'default',
  resuelto: 'secondary',
  descartado: 'destructive',
}

export default function PaginaModeracionAdmin() {
  const [reportes, setReportes] = useState<ReporteAdmin[]>([])
  const [filtro, setFiltro] = useState('pendiente')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    const cargarReportes = async () => {
      setCargando(true)
      try {
        const params = filtro === 'todos' ? {} : { estado: filtro }
        const { data } = await api.get<ReporteAdmin[]>('/moderacion/reportes/', { params })
        setReportes(data)
      } catch {
        toast.error('No se pudieron cargar los reportes')
      } finally {
        setCargando(false)
      }
    }
    cargarReportes()
  }, [filtro])

  // Cambia el estado de un reporte y lo retira de la lista si ya no coincide con el filtro activo.
  const cambiarEstado = async (id: number, estado: EstadoReporte) => {
    try {
      await api.patch(`/moderacion/reportes/${id}/`, { estado })
      setReportes((prev) =>
        filtro === 'todos'
          ? prev.map((r) => (r.id === id ? { ...r, estado } : r))
          : prev.filter((r) => r.id !== id)
      )
      toast.success('Reporte actualizado')
    } catch {
      toast.error('No se pudo actualizar el reporte')
    }
  }

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Moderación</h2>
          <p className="text-muted-foreground">
            Reportes de cursos y exámenes enviados por docentes y estudiantes
          </p>
        </div>
        <Select value={filtro} onValueChange={(v) => v && setFiltro(v)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {filtros.map((f) => (
              <SelectItem key={f.value} value={f.value}>
                {f.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Estado de carga */}
      {cargando && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      )}

      {/* Estado vacío */}
      {!cargando && reportes.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Flag className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No hay reportes {filtro !== 'todos' ? filtros.find((f) => f.value === filtro)?.label.toLowerCase() : ''}
          </p>
        </div>
      )}

      {/* Tabla de reportes */}
      {!cargando && reportes.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Motivo</TableHead>
              <TableHead>Reportado</TableHead>
              <TableHead className="hidden md:table-cell">Por</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reportes.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="max-w-xs">
                  <p className="line-clamp-2 text-sm">{r.motivo}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(r.creado_en).toLocaleString()}
                  </p>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5 text-sm">
                    {r.examen ? (
                      <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    ) : (
                      <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    )}
                    <span className="truncate">
                      {r.examen_titulo ?? r.curso_nombre ?? '—'}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="hidden md:table-cell text-muted-foreground">
                  {r.reportado_por}
                </TableCell>
                <TableCell>
                  <Badge variant={estiloEstado[r.estado]} className="capitalize">
                    {r.estado}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {r.estado === 'pendiente' ? (
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-muted-foreground hover:text-emerald-600"
                        title="Marcar como resuelto"
                        onClick={() => cambiarEstado(r.id, 'resuelto')}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-muted-foreground hover:text-destructive"
                        title="Descartar"
                        onClick={() => cambiarEstado(r.id, 'descartado')}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:text-foreground"
                      title="Reabrir"
                      onClick={() => cambiarEstado(r.id, 'pendiente')}
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
