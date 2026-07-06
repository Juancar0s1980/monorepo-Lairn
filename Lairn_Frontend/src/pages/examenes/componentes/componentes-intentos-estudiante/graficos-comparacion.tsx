// Gráficos agrupados de comparación por concepto y dificultad para N intentos.
//
// Se usa en la vista de comparación debajo de las cards de intento.
// Cada intento se representa con una barra de color distinto de la colimetría púrpura.

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
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
import { calcularAciertos, coloresIntentos } from '../../utilidades'

export function GraficosComparacion({
  intentosSeleccionados,
  intentosComparar,
}: {
  intentosSeleccionados: Resultado[]
  intentosComparar: number[]
}) {
  // ChartConfig dinámico según cantidad de intentos seleccionados.
  const chartConfigComparacion: ChartConfig = {}
  intentosSeleccionados.forEach((_, i) => {
    chartConfigComparacion[`aciertos_${i}`] = {
      label: `Intento #${intentosComparar[i] + 1}`,
      color: coloresIntentos[i % coloresIntentos.length],
    }
  })

  // Helper para generar datos de comparación agrupados.
  const generarDatos = (
    campo: 'concepto' | 'dificultad'
  ): Record<string, string | number>[] => {
    const mapasPorIntento = intentosSeleccionados.map((int) =>
      calcularAciertos(int.respuestas, campo)
    )

    if (campo === 'concepto') {
      // Unión de todos los conceptos.
      const todosConceptos = new Set<string>()
      for (const mapa of mapasPorIntento) {
        for (const clave of mapa.keys()) {
          todosConceptos.add(clave as string)
        }
      }
      return Array.from(todosConceptos)
        .map((concepto) => {
          const fila: Record<string, string | number> = {
            concepto:
              concepto.length > 25 ? concepto.slice(0, 25) + '…' : concepto,
          }
          let suma = 0
          mapasPorIntento.forEach((mapa, i) => {
            const datos = mapa.get(concepto)
            const pct = datos
              ? Math.round((datos.correctas / datos.total) * 100)
              : 0
            fila[`aciertos_${i}`] = pct
            suma += pct
          })
          fila._promedio = suma / mapasPorIntento.length
          return fila
        })
        .sort((a, b) => (b._promedio as number) - (a._promedio as number))
        .slice(0, 8)
    }

    // Dificultad
    return [1, 2, 3].map((d) => {
      const fila: Record<string, string | number> = {
        dificultad:
          d === 1 ? 'Básico' : d === 2 ? 'Intermedio' : 'Avanzado',
      }
      mapasPorIntento.forEach((mapa, i) => {
        const datos = mapa.get(d)
        fila[`aciertos_${i}`] = datos
          ? Math.round((datos.correctas / datos.total) * 100)
          : 0
      })
      return fila
    })
  }

  const datosConceptos = generarDatos('concepto')
  const datosDificultad = generarDatos('dificultad')

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* Aciertos por concepto — comparación */}
      <Card>
        <CardHeader>
          <CardTitle>Aciertos por concepto</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfigComparacion}
            className="h-[280px] w-full"
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
                tick={{
                  fontSize: 12,
                  fill: 'var(--muted-foreground)',
                }}
              />
              <YAxis
                type="category"
                dataKey="concepto"
                width={130}
                tick={{
                  fontSize: 11,
                  fill: 'var(--muted-foreground)',
                }}
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
              {intentosSeleccionados.map((_, i) => (
                <Bar
                  key={i}
                  dataKey={`aciertos_${i}`}
                  fill={coloresIntentos[i % coloresIntentos.length]}
                  radius={[0, 4, 4, 0]}
                  name={`Intento #${intentosComparar[i] + 1}`}
                />
              ))}
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Dificultad vs acierto — comparación */}
      <Card>
        <CardHeader>
          <CardTitle>Dificultad vs acierto</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfigComparacion}
            className="h-[280px] w-full"
          >
            <BarChart data={datosDificultad}>
              <CartesianGrid
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="dificultad"
                tick={{
                  fontSize: 12,
                  fill: 'var(--muted-foreground)',
                }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{
                  fontSize: 12,
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
              {intentosSeleccionados.map((_, i) => (
                <Bar
                  key={i}
                  dataKey={`aciertos_${i}`}
                  fill={coloresIntentos[i % coloresIntentos.length]}
                  radius={[4, 4, 0, 0]}
                  name={`Intento #${intentosComparar[i] + 1}`}
                />
              ))}
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}
