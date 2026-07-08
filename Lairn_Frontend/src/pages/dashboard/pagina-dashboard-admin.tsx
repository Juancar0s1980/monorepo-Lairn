// Dashboard del Administrador.
// Muestra métricas rápidas del sistema y accesos directos a las secciones de
// gestión (usuarios, exámenes, analítica), además de la actividad más
// reciente (últimos cursos y exámenes creados, últimos resultados).
// Obtiene los datos de GET /analitica/administracion/resumen/.

import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CardStat } from '@/components/card-stat'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Calendar,
  FileText,
  GraduationCap,
  TrendingUp,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import type { ResumenGlobalAdmin } from '@/types/analitica'

// Formatea la fecha actual en español.
function formatearFecha(): string {
  return new Date().toLocaleDateString('es-CO', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

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

export default function PaginaDashboardAdmin() {
  const [resumen, setResumen] = useState<ResumenGlobalAdmin | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const { data } = await api.get<ResumenGlobalAdmin>('/analitica/administracion/resumen/')
        setResumen(data)
      } catch {
        setError('No se pudo cargar el estado del sistema')
        toast.error('No se pudo cargar el estado del sistema')
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
        <div className="grid gap-4 lg:grid-cols-3">
          <SkeletonCard className="h-56" />
          <SkeletonCard className="h-56" />
          <SkeletonCard className="h-56" />
        </div>
      </div>
    )
  }

  if (error || !resumen) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {error ?? 'No se pudo cargar el dashboard'}
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
        titulo="Dashboard"
        subtitulo={
          <span className="flex items-center gap-1.5 capitalize">
            <Calendar className="h-3.5 w-3.5" />
            {formatearFecha()}
          </span>
        }
      />

      {/* Stats rápidas */}
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

      {/* Accesos rápidos */}
      <div className="grid gap-2 sm:grid-cols-3">
        <Link to="/usuarios">
          <Button variant="outline" className="w-full justify-between">
            Gestionar usuarios
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
        <Link to="/examenes">
          <Button variant="outline" className="w-full justify-between">
            Ver exámenes
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
        <Link to="/analitica">
          <Button variant="outline" className="w-full justify-between">
            Ver analítica
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </div>

      {/* Actividad reciente */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-sm font-semibold">Cursos recientes</h3>
            {resumen.cursos_recientes.length === 0 && (
              <p className="text-xs text-muted-foreground">Sin cursos aún</p>
            )}
            <ul className="space-y-2.5">
              {resumen.cursos_recientes.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{c.nombre}</p>
                    <p className="truncate text-xs text-muted-foreground">{c.docente}</p>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {new Date(c.creado_en).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-sm font-semibold">Exámenes recientes</h3>
            {resumen.examenes_recientes.length === 0 && (
              <p className="text-xs text-muted-foreground">Sin exámenes aún</p>
            )}
            <ul className="space-y-2.5">
              {resumen.examenes_recientes.map((e) => (
                <li key={e.id} className="flex items-center justify-between gap-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{e.titulo}</p>
                    <p className="truncate text-xs text-muted-foreground">{e.curso}</p>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {new Date(e.creado_en).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-sm font-semibold">Resultados recientes</h3>
            {resumen.resultados_recientes.length === 0 && (
              <p className="text-xs text-muted-foreground">Sin resultados aún</p>
            )}
            <ul className="space-y-2.5">
              {resumen.resultados_recientes.map((r, i) => (
                <li key={i} className="flex items-center justify-between gap-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{r.estudiante}</p>
                    <p className="truncate text-xs text-muted-foreground">{r.examen}</p>
                  </div>
                  <span className="shrink-0 flex items-center gap-1 text-xs">
                    <FileText className="h-3 w-3 text-muted-foreground" />
                    {r.nota.toFixed(1)}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
