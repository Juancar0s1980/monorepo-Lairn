// Evaluaciones que el docente supervisa en sala (ADR-009): publicadas, sin
// cerrar o cerradas hace menos de un día. Cada tarjeta abre el llamado a lista.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ClipboardList, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SupervisionDocente } from '@/types/supervision'
import { mensajeError } from '@/pages/academico/academico-utils'
import { formatoFecha, useConsultaPeriodica } from './supervision-utils'

function estadoVentana(e: SupervisionDocente): { texto: string; clase: string } {
  const ahora = Date.now()
  if (new Date(e.fecha_fin).getTime() < ahora) return { texto: 'Cerrada', clase: 'bg-muted text-muted-foreground' }
  if (new Date(e.fecha_inicio).getTime() <= ahora) return { texto: 'Abierta', clase: 'bg-success/10 text-success' }
  return { texto: 'Próxima', clase: 'bg-primary/10 text-primary' }
}

export default function PaginaSupervision() {
  const [lista, setLista] = useState<SupervisionDocente[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useConsultaPeriodica(async () => {
    try {
      const r = await api.get<SupervisionDocente[]>('/evaluacion/docente/supervision/')
      setLista(r.data)
      setError('')
    } catch (err: unknown) {
      setError(mensajeError(err, 'No se pudieron cargar tus supervisiones.'))
    } finally {
      setCargando(false)
    }
  })

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Panel del docente"
        titulo="Supervisión en sala"
        subtitulo="Evaluaciones formales en las que te asignaron como supervisor. Haz el llamado a lista para habilitar a cada estudiante."
      />
      {cargando ? (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
        </div>
      ) : error ? (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      ) : lista.length === 0 ? (
        <Card>
          <CardContent className="space-y-2 p-6 text-sm">
            <ClipboardList className="h-8 w-8 text-primary" aria-hidden />
            <p className="font-medium text-foreground">No tienes evaluaciones por supervisar</p>
            <p className="text-muted-foreground">Cuando el coordinador te asigne una evaluación aparecerá aquí.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {lista.map((e) => {
            const estado = estadoVentana(e)
            const llamados = e.conteos.convocados - e.conteos.sin_llamar
            return (
              <Link
                key={e.id}
                to={`/supervision/${e.id}`}
                className="block space-y-2 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-foreground">{e.nombre}</span>
                  <Badge className={cn('shrink-0 border-transparent', estado.clase)}>{estado.texto}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {e.programa} · {e.momento}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatoFecha.format(new Date(e.fecha_inicio))} → {formatoFecha.format(new Date(e.fecha_fin))} ·{' '}
                  {e.duracion_minutos} min
                </p>
                <p className="text-sm text-foreground">
                  Llamado a lista: {llamados} de {e.conteos.convocados} · {e.conteos.en_curso} en curso ·{' '}
                  {e.conteos.enviados} enviadas
                </p>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
