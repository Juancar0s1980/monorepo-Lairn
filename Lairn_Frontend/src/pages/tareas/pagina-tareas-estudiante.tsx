// Tareas del estudiante (HU-08A.1 / 08A.3): tareas publicadas de sus cursos,
// con fecha límite, tiempo restante y estado de su entrega o nota.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ClipboardList, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TareaEstudiante } from '@/types/tarea'
import { mensajeError } from '@/pages/academico/academico-utils'
import { ETIQUETA_ENTREGA, formatoFecha, tiempoRestante } from './utilidades-tareas'

export default function PaginaTareasEstudiante() {
  const [tareas, setTareas] = useState<TareaEstudiante[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<TareaEstudiante[]>('/evaluacion/estudiante/tareas/')
        if (activo) setTareas(res.data)
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se pudieron cargar tus tareas.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [])

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Panel del estudiante"
        titulo="Tareas"
        subtitulo="Consulta las instrucciones, la rúbrica y el plazo de cada tarea, y envía tu entrega."
      />
      {cargando ? (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
        </div>
      ) : error ? (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      ) : tareas.length === 0 ? (
        <Card>
          <CardContent className="space-y-2 p-6 text-sm">
            <ClipboardList className="h-8 w-8 text-primary" aria-hidden />
            <p className="font-medium text-foreground">No tienes tareas asignadas</p>
            <p className="text-muted-foreground">Cuando tus docentes publiquen tareas en tus cursos aparecerán aquí.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {tareas.map((t) => {
            const estado = t.mi_entrega?.estado ?? 'sin_entregar'
            const nota = t.mi_entrega?.calificacion?.nota
            return (
              <Link
                key={t.id}
                to={`/mis-tareas/${t.id}`}
                className="block rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-foreground">{t.titulo}</span>
                  <Badge className={cn('shrink-0 border-transparent', ETIQUETA_ENTREGA[estado].clase)}>
                    {nota ? `Nota ${nota}` : ETIQUETA_ENTREGA[estado].texto}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {t.asignatura.codigo} — {t.asignatura.nombre}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Entrega: {formatoFecha.format(new Date(t.fecha_limite))}
                  {!t.mi_entrega && (
                    <span className={cn('ml-1 font-medium', t.estado_plazo === 'abierta' ? 'text-primary' : 'text-destructive')}>
                      · {t.estado_plazo === 'cerrada' ? 'Cerrada' : tiempoRestante(t.fecha_limite)}
                    </span>
                  )}
                </p>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
