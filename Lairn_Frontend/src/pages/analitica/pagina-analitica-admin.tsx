// Analítica global del sistema (solo accesible para Administrador).
// Muestra métricas agregadas (usuarios, cursos, exámenes, rendimiento) y una
// tabla comparativa de rendimiento por curso, ordenada de menor a mayor nota
// promedio para resaltar los cursos que requieren atención.
// Obtiene los datos de GET /analitica/administracion/resumen/ y
// GET /analitica/administracion/cursos/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { CardStat } from '@/components/card-stat'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AlertCircle,
  BookOpen,
  FileText,
  GraduationCap,
  TrendingUp,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import type { ResumenGlobalAdmin, CursoRendimientoAdmin } from '@/types/analitica'

function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="h-8 w-16 rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function PaginaAnaliticaAdmin() {
  const [resumen, setResumen] = useState<ResumenGlobalAdmin | null>(null)
  const [cursos, setCursos] = useState<CursoRendimientoAdmin[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [resResumen, resCursos] = await Promise.all([
          api.get<ResumenGlobalAdmin>('/analitica/administracion/resumen/'),
          api.get<CursoRendimientoAdmin[]>('/analitica/administracion/cursos/'),
        ])
        setResumen(resResumen.data)
        setCursos(
          [...resCursos.data].sort((a, b) => a.nota_promedio - b.nota_promedio)
        )
      } catch {
        setError('No se pudo cargar la analítica del sistema')
        toast.error('No se pudo cargar la analítica del sistema')
      } finally {
        setCargando(false)
      }
    }
    cargarDatos()
  }, [])

  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-2">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-4 w-48 rounded bg-muted" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <SkeletonCard className="h-64" />
      </div>
    )
  }

  if (error || !resumen) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {error ?? 'No se pudo cargar la analítica'}
        </p>
      </div>
    )
  }

  const totalUsuarios =
    resumen.usuarios_por_rol.administrador +
    resumen.usuarios_por_rol.docente +
    resumen.usuarios_por_rol.estudiante

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Panel del administrador"
        titulo="Analítica"
        subtitulo="Métricas globales y rendimiento por curso de todo el sistema"
      />

      {/* Stats globales */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <CardStat
          titulo="Usuarios"
          valor={totalUsuarios}
          icono={Users}
          variante="primary"
          subtitulo={`${resumen.usuarios_por_rol.docente} docentes, ${resumen.usuarios_por_rol.estudiante} estudiantes`}
        />
        <CardStat
          titulo="Cursos"
          valor={resumen.total_cursos}
          icono={BookOpen}
          subtitulo={`${resumen.total_examenes} exámenes en total`}
        />
        <CardStat
          titulo="Nota promedio global"
          valor={resumen.nota_promedio_global.toFixed(1)}
          icono={TrendingUp}
          variante="exito"
          subtitulo={`${resumen.tasa_aprobados_global}% de aprobación`}
        />
        <CardStat
          titulo="Sesiones activas"
          valor={resumen.sesiones_en_progreso}
          icono={GraduationCap}
          subtitulo={`${resumen.sesiones_completadas} completadas`}
        />
      </div>

      {/* Rendimiento por curso */}
      <div className="space-y-3">
        <h3 className="font-heading text-lg">Rendimiento por curso</h3>

        {cursos.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <FileText className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              Aún no hay cursos en el sistema
            </p>
          </div>
        )}

        {cursos.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Curso</TableHead>
                <TableHead className="hidden md:table-cell">Docente</TableHead>
                <TableHead>Inscritos</TableHead>
                <TableHead className="hidden sm:table-cell">Exámenes</TableHead>
                <TableHead>Nota promedio</TableHead>
                <TableHead className="hidden sm:table-cell">Aprobados</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cursos.map((curso) => (
                <TableRow key={curso.id}>
                  <TableCell>
                    <p className="font-medium">{curso.nombre}</p>
                    <p className="text-xs text-muted-foreground">{curso.codigo}</p>
                  </TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground">
                    {curso.docente}
                  </TableCell>
                  <TableCell>{curso.total_inscritos}</TableCell>
                  <TableCell className="hidden sm:table-cell">
                    {curso.total_examenes}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        curso.nota_promedio >= 4.0
                          ? 'default'
                          : curso.nota_promedio >= 3.0
                            ? 'secondary'
                            : 'destructive'
                      }
                    >
                      {curso.nota_promedio.toFixed(1)}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">
                    {curso.tasa_aprobados}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
