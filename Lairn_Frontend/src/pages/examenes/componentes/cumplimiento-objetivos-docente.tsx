// Sección de cumplimiento de objetivos por examen (tab Analítica del docente).
//
// Para cada examen del curso con objetivos anclados muestra:
//   - Resumen del examen: cuántos objetivos están cumplidos.
//   - Por objetivo: estado (cumplido / en proceso / no cumplido / sin datos),
//     % de acierto de las preguntas que lo evaluaron, cuántos estudiantes lo
//     dominan y el nivel promedio (1-3, del Knowledge Tracing).
//
// Datos de GET /analitica/curso/{cursoId}/objetivos/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Loader2, Target, TrendingUp, Users } from 'lucide-react'

type EstadoObjetivo = 'cumplido' | 'en_proceso' | 'no_cumplido' | 'sin_datos'

interface ObjetivoStats {
  objetivo_id: number
  objetivo: string
  preguntas_respondidas: number
  correctas: number
  porcentaje_acierto: number | null
  estudiantes_evaluados: number
  estudiantes_dominan: number
  nivel_promedio: number | null
  estado: EstadoObjetivo
}

interface ExamenObjetivos {
  examen_id: number
  titulo: string
  objetivos: ObjetivoStats[]
  resumen: {
    total_objetivos: number
    cumplido: number
    en_proceso: number
    no_cumplido: number
    sin_datos: number
    porcentaje_cumplimiento: number
  }
}

interface RespuestaCumplimiento {
  curso: string
  examenes: ExamenObjetivos[]
  resumen_global: ExamenObjetivos['resumen'] & { total_objetivos_evaluados: number }
}

// Configuración visual por estado del objetivo.
const estadoConfig: Record<EstadoObjetivo, { label: string; badge: 'default' | 'secondary' | 'destructive' | 'outline'; barra: string }> = {
  cumplido: { label: 'Cumplido', badge: 'default', barra: 'bg-emerald-500' },
  en_proceso: { label: 'En proceso', badge: 'secondary', barra: 'bg-amber-500' },
  no_cumplido: { label: 'No cumplido', badge: 'destructive', barra: 'bg-red-500' },
  sin_datos: { label: 'Sin datos', badge: 'outline', barra: 'bg-muted-foreground/30' },
}

interface CumplimientoObjetivosDocenteProps {
  cursoId: string
}

export function CumplimientoObjetivosDocente({ cursoId }: CumplimientoObjetivosDocenteProps) {
  const [datos, setDatos] = useState<RespuestaCumplimiento | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<RespuestaCumplimiento>(
          `/analitica/curso/${cursoId}/objetivos/`,
          { signal: controlador.signal }
        )
        setDatos(data)
      } catch {
        // Sección opcional: si falla, simplemente no se muestra.
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId])

  if (cargando) {
    return (
      <div className="flex h-24 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Sin exámenes anclados a objetivos: no hay nada que reportar.
  if (!datos || datos.examenes.length === 0) return null

  const g = datos.resumen_global

  return (
    <div className="space-y-4">
      {/* Encabezado de la sección con resumen global del curso */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="flex items-center gap-2 font-heading text-lg">
          <Target className="h-4 w-4 text-muted-foreground" />
          Cumplimiento de objetivos
        </h3>
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{g.cumplido}</span> de{' '}
          {g.total_objetivos_evaluados} objetivo(s) cumplidos en el curso ({g.porcentaje_cumplimiento}%)
        </p>
      </div>

      {/* Un card por examen con objetivos anclados */}
      {datos.examenes.map((examen) => (
        <Card key={examen.examen_id}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-base">{examen.titulo}</CardTitle>
              <Badge variant={examen.resumen.cumplido === examen.resumen.total_objetivos ? 'default' : 'secondary'}>
                <CheckCircle2 className="h-3 w-3" />
                {examen.resumen.cumplido}/{examen.resumen.total_objetivos} cumplidos
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {examen.objetivos.map((objetivo) => {
              const config = estadoConfig[objetivo.estado]
              const acierto = objetivo.porcentaje_acierto ?? 0
              return (
                <div key={objetivo.objetivo_id} className="space-y-1.5">
                  {/* Descripción + estado */}
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm">{objetivo.objetivo}</p>
                    <Badge variant={config.badge} className="shrink-0">
                      {config.label}
                    </Badge>
                  </div>

                  {/* Barra de % de acierto */}
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${config.barra}`}
                      style={{ width: `${acierto}%` }}
                    />
                  </div>

                  {/* Métricas del objetivo */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>
                      {objetivo.porcentaje_acierto !== null
                        ? `${objetivo.porcentaje_acierto}% de acierto (${objetivo.correctas}/${objetivo.preguntas_respondidas} preguntas)`
                        : 'Aún sin preguntas respondidas'}
                    </span>
                    {objetivo.estudiantes_evaluados > 0 && (
                      <>
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {objetivo.estudiantes_dominan}/{objetivo.estudiantes_evaluados} lo dominan
                        </span>
                        {objetivo.nivel_promedio !== null && (
                          <span className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            nivel {objetivo.nivel_promedio.toFixed(1)}/3
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
