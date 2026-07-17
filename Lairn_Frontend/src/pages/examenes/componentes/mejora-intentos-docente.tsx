// Mejora entre intentos por examen (tab Analítica del docente).
//
// Para exámenes donde algún estudiante presentó más de un intento, compara
// nota promedio por número de intento y cuántos estudiantes mejoraron entre
// su primer y su último intento — responde si repetir el examen realmente
// ayuda a aprender o los estudiantes se estancan.
//
// Datos de GET /analitica/curso/{cursoId}/mejora-intentos/.

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
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ReferenceLine, Label } from 'recharts'
import { Loader2, Repeat } from 'lucide-react'
import type { MejoraIntentosCurso } from '@/types/analitica'

const chartConfig = {
  nota_promedio: { label: 'Nota promedio', color: 'var(--purple-4)' },
} satisfies ChartConfig

interface MejoraIntentosDocenteProps {
  cursoId: string
}

export function MejoraIntentosDocente({ cursoId }: MejoraIntentosDocenteProps) {
  const [datos, setDatos] = useState<MejoraIntentosCurso | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<MejoraIntentosCurso>(
          `/analitica/curso/${cursoId}/mejora-intentos/`,
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

  // Sin exámenes con reintentos reales: no hay nada que comparar.
  if (!datos || datos.examenes.length === 0) return null

  return (
    <div className="space-y-4">
      <h3 className="flex items-center gap-2 font-heading text-lg">
        <Repeat className="h-4 w-4 text-muted-foreground" />
        Mejora entre intentos
      </h3>

      <div className="grid gap-4 sm:grid-cols-2">
        {datos.examenes.map((examen) => {
          const datosGrafico = examen.intentos.map((i) => ({
            intento: `Intento ${i.intento}`,
            nota_promedio: i.nota_promedio,
          }))
          return (
            <Card key={examen.examen_id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm line-clamp-1">{examen.titulo}</CardTitle>
                  {examen.mejora_promedio !== null && (
                    <Badge variant={examen.mejora_promedio > 0 ? 'default' : 'destructive'}>
                      {examen.mejora_promedio > 0 ? '+' : ''}
                      {examen.mejora_promedio.toFixed(1)} promedio
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3 pt-2">
                <ChartContainer config={chartConfig} className="h-[180px] w-full">
                  <BarChart data={datosGrafico}>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis
                      dataKey="intento"
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
                    <Bar dataKey="nota_promedio" fill="var(--color-nota_promedio)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ChartContainer>
                <p className="text-xs text-muted-foreground">
                  <span className="font-semibold text-foreground">
                    {examen.estudiantes_mejoraron}/{examen.estudiantes_con_reintento}
                  </span>{' '}
                  estudiantes mejoraron su nota entre el primer y el último intento
                  {examen.estudiantes_empeoraron > 0 && (
                    <> · {examen.estudiantes_empeoraron} empeoraron</>
                  )}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
