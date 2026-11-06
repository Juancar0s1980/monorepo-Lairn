// Evaluaciones formales del estudiante (HU-07.1): solo las activas a las que
// está convocado, más las que ya presentó como constancia.
// ADR-009: si exige llamado a lista y aún no te habilitan, la tarjeta lo indica
// y la lista se re-consulta cada 10 s.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ClipboardCheck, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { bloqueoPorAsistencia, type EvaluacionEstudiante } from '@/types/presentacion'
import { mensajeError } from '@/pages/academico/academico-utils'

const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

function estadoVisible(e: EvaluacionEstudiante): { texto: string; clase: string } {
  if (e.intento?.integridad === 'anulado_fraude') return { texto: 'Anulada', clase: 'bg-destructive/10 text-destructive' }
  if (e.intento?.integridad === 'suspendido') return { texto: 'Suspendida', clase: 'bg-destructive/10 text-destructive' }
  if (e.intento?.estado === 'enviado') return { texto: 'Enviada', clase: 'bg-success/10 text-success' }
  if (e.intento?.estado === 'en_curso') return { texto: 'En curso', clase: 'bg-warning/15 text-foreground' }
  const bloqueo = e.tipo === 'cuestionario' ? bloqueoPorAsistencia(e) : null
  if (bloqueo === 'Esperando llamado a lista') return { texto: bloqueo, clase: 'bg-muted text-muted-foreground' }
  if (bloqueo) return { texto: bloqueo, clase: 'bg-destructive/10 text-destructive' }
  return { texto: 'Disponible', clase: 'bg-primary/10 text-primary' }
}

export default function PaginaEvaluacionesEstudiante() {
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionEstudiante[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<EvaluacionEstudiante[]>('/evaluacion/estudiante/evaluaciones/')
        if (activo) setEvaluaciones(res.data)
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se pudieron cargar tus evaluaciones.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    // Re-consulta periódica: refleja el llamado a lista sin recargar la página.
    const id = window.setInterval(cargar, 10_000)
    return () => {
      activo = false
      window.clearInterval(id)
    }
  }, [])

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Panel del estudiante"
        titulo="Evaluaciones formales"
        subtitulo="Evaluaciones de resultados de aprendizaje a las que estás convocado y que están abiertas ahora."
      />
      {cargando ? (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
        </div>
      ) : error ? (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      ) : evaluaciones.length === 0 ? (
        <Card>
          <CardContent className="space-y-2 p-6 text-sm">
            <ClipboardCheck className="h-8 w-8 text-primary" aria-hidden />
            <p className="font-medium text-foreground">No tienes evaluaciones abiertas</p>
            <p className="text-muted-foreground">Cuando se abra una evaluación formal de tus cursos aparecerá aquí.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {evaluaciones.map((e) => {
            const estado = estadoVisible(e)
            const destino = e.tipo === 'tarea' && e.tarea ? `/mis-tareas/${e.tarea.id}` : `/mis-evaluaciones/${e.id}`
            return (
              <Link
                key={e.id}
                to={destino}
                className="block rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-foreground">{e.nombre}</span>
                  <Badge className={cn('shrink-0 border-transparent', estado.clase)}>{estado.texto}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{e.momento}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {e.tipo === 'tarea'
                    ? `Se presenta entregando la tarea "${e.tarea?.titulo}"`
                    : `${e.total_preguntas} preguntas · ${e.duracion_minutos} min`}
                </p>
                <p className="text-xs text-muted-foreground">Cierra: {formatoFecha.format(new Date(e.fecha_fin))}</p>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
