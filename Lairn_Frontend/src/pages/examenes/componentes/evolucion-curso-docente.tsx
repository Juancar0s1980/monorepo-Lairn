// Evolución de la nota del curso en el tiempo (tab Analítica del docente).
//
// Agrupa los resultados por semana y grafica la nota promedio, para ver si
// el grupo mejora, empeora o se mantiene estable — algo que las demás
// secciones (fotos fijas) no muestran.
//
// Datos de GET /analitica/curso/{cursoId}/evolucion/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine, Label } from 'recharts'
import { Loader2, TrendingDown, TrendingUp, Minus } from 'lucide-react'
import type { EvolucionCurso } from '@/types/analitica'

const tendenciaConfig = {
  mejorando: { label: 'Mejorando', icon: TrendingUp, badge: 'default' as const },
  empeorando: { label: 'Empeorando', icon: TrendingDown, badge: 'destructive' as const },
  estable: { label: 'Estable', icon: Minus, badge: 'secondary' as const },
}

const chartConfig = {
  nota_promedio: { label: 'Nota promedio', color: 'var(--purple-2)' },
} satisfies ChartConfig

interface EvolucionCursoDocenteProps {
  cursoId: string
}

export function EvolucionCursoDocente({ cursoId }: EvolucionCursoDocenteProps) {
  const [datos, setDatos] = useState<EvolucionCurso | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<EvolucionCurso>(
          `/analitica/curso/${cursoId}/evolucion/`,
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

  // Necesita al menos 2 semanas con datos para que una tendencia tenga sentido.
  if (!datos || datos.puntos.length < 2) return null

  const config = datos.tendencia ? tendenciaConfig[datos.tendencia] : null

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm">Evolución de la nota en el tiempo</CardTitle>
          {config && (
            <Badge variant={config.badge}>
              <config.icon className="h-3 w-3" />
              {config.label}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        <ChartContainer config={chartConfig} className="h-[220px] w-full">
          <LineChart data={datos.puntos}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="periodo"
              tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
            />
            <YAxis
              domain={[1, 5]}
              tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
            />
            <ReferenceLine
              y={3}
              stroke="var(--muted-foreground)"
              strokeDasharray="4 4"
              strokeOpacity={0.4}
            >
              <Label value="Aprobado" position="insideTopRight" fontSize={10} fill="var(--muted-foreground)" />
            </ReferenceLine>
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              type="monotone"
              dataKey="nota_promedio"
              stroke="var(--color-nota_promedio)"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
