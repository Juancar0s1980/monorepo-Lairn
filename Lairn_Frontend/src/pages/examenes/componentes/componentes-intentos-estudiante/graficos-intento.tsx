// Gráficos de aciertos por concepto y dificultad para un intento individual.
//
// Se usa en la vista individual (no comparación) al lado de la CardIntento.

import { useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  Label,
} from 'recharts'
import type { Resultado } from '@/types/analitica'
import { chartConfig } from '../../utilidades'

export function GraficosIntento({
  intento,
}: {
  intento: Resultado
}) {
  // Datos para gráfico de aciertos por concepto.
  const datosConceptos = useMemo(() => {
    const conceptosMap = new Map<
      string,
      { correctas: number; total: number }
    >()
    for (const resp of intento.respuestas) {
      const actual = conceptosMap.get(resp.concepto) ?? {
        correctas: 0,
        total: 0,
      }
      const esCorrecta = !resp.respuesta_incorrecta
      conceptosMap.set(resp.concepto, {
        correctas: actual.correctas + (esCorrecta ? 1 : 0),
        total: actual.total + 1,
      })
    }
    return Array.from(conceptosMap.entries())
      .map(([concepto, datos]) => ({
        concepto:
          concepto.length > 25 ? concepto.slice(0, 25) + '…' : concepto,
        aciertos: Math.round((datos.correctas / datos.total) * 100),
      }))
      .sort((a, b) => b.aciertos - a.aciertos)
      .slice(0, 5)
  }, [intento])

  // Datos para gráfico de dificultad vs acierto.
  const datosDificultad = useMemo(() => {
    const dificultadMap = new Map<
      number,
      { correctas: number; total: number }
    >()
    for (const resp of intento.respuestas) {
      const actual = dificultadMap.get(resp.dificultad) ?? {
        correctas: 0,
        total: 0,
      }
      const esCorrecta = !resp.respuesta_incorrecta
      dificultadMap.set(resp.dificultad, {
        correctas: actual.correctas + (esCorrecta ? 1 : 0),
        total: actual.total + 1,
      })
    }
    return [1, 2, 3].map((d) => {
      const datos = dificultadMap.get(d)
      return {
        dificultad:
          d === 1 ? 'Básico' : d === 2 ? 'Intermedio' : 'Avanzado',
        aciertos: datos
          ? Math.round((datos.correctas / datos.total) * 100)
          : 0,
      }
    })
  }, [intento])

  return (
    <>
      {/* Aciertos por concepto */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Aciertos por concepto</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfig}
            className="h-[220px] w-full"
          >
            <BarChart data={datosConceptos} layout="vertical">
              <CartesianGrid
                stroke="var(--border)"
                vertical={false}
                horizontal={false}
              />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
              />
              <YAxis
                type="category"
                dataKey="concepto"
                width={120}
                tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
              />
              <ReferenceLine
                x={60}
                stroke="var(--muted-foreground)"
                strokeDasharray="4 4"
                strokeOpacity={0.4}
              >
                <Label
                  value="Aprobado"
                  position="insideTop"
                  fontSize={10}
                  fill="var(--muted-foreground)"
                />
              </ReferenceLine>
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="aciertos"
                fill="var(--color-aciertos)"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Dificultad vs acierto */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Dificultad vs acierto</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfig}
            className="h-[220px] w-full"
          >
            <BarChart data={datosDificultad}>
              <CartesianGrid
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="dificultad"
                tick={{
                  fontSize: 11,
                  fill: 'var(--muted-foreground)',
                }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{
                  fontSize: 11,
                  fill: 'var(--muted-foreground)',
                }}
              />
              <ReferenceLine
                y={60}
                stroke="var(--muted-foreground)"
                strokeDasharray="4 4"
                strokeOpacity={0.4}
              >
                <Label
                  value="Aprobado"
                  position="insideTopRight"
                  fontSize={10}
                  fill="var(--muted-foreground)"
                />
              </ReferenceLine>
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="aciertos"
                fill="var(--color-aciertos)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </>
  )
}
