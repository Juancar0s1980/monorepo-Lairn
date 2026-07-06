// Tab de intento individual para el estudiante.
//
// Permite seleccionar un examen y ver el detalle de cada intento.
// Usa el endpoint: GET /api/analitica/mis-resultados/examen/{examen_id}/
// Incluye modo comparación cuando hay 2+ intentos.

import { useState, useMemo } from 'react'
import api from '@/services/api'
import { Loader2, Hash, GitCompareArrows } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import type { Resultado, ResultadosExamen } from '@/types/analitica'
import { coloresIntentos } from '../utilidades'
import { CardIntento } from './componentes-intentos-estudiante/card-intento'
import { GraficosIntento } from './componentes-intentos-estudiante/graficos-intento'
import { GraficosComparacion } from './componentes-intentos-estudiante/graficos-comparacion'
import { TablaRespuestas } from './componentes-intentos-estudiante/tabla-respuestas'

export function TabIntentoEstudiante({
  resultados,
}: {
  resultados: Resultado[]
}) {
  // Examen seleccionado en el dropdown.
  const [examenSeleccionado, setExamenSeleccionado] = useState<number | null>(
    null
  )
  // Datos del endpoint individual.
  const [datosExamen, setDatosExamen] = useState<ResultadosExamen | null>(null)
  // Intento seleccionado dentro del examen.
  const [intentoIdx, setIntentoIdx] = useState(0)
  // Estado de carga.
  const [cargando, setCargando] = useState(false)
  // Modo comparación.
  const [modoComparar, setModoComparar] = useState(false)
  // Intentos seleccionados para comparar (índices).
  const [intentosComparar, setIntentosComparar] = useState<number[]>([])

  // Exámenes únicos extraídos de los resultados del avance global.
  const examenesUnicos = useMemo(() => {
    const mapa = new Map<number, number>()
    for (const r of resultados) {
      if (!mapa.has(r.examen)) {
        mapa.set(r.examen, r.id)
      }
    }
    return Array.from(mapa.entries()).map(([examenId]) => examenId)
  }, [resultados])

  // Carga los datos de un examen individual.
  const cargarExamen = async (examenId: number) => {
    setExamenSeleccionado(examenId)
    setCargando(true)
    setIntentoIdx(0)
    setModoComparar(false)
    setIntentosComparar([])
    try {
      const { data } = await api.get<ResultadosExamen>(
        `/analitica/mis-resultados/examen/${examenId}/`
      )
      setDatosExamen(data)
    } catch {
      toast.error('No se pudieron cargar los datos del examen')
      setDatosExamen(null)
    } finally {
      setCargando(false)
    }
  }

  // Intento actualmente seleccionado.
  const intentoActual = datosExamen?.resultados[intentoIdx] ?? null

  // Intentos seleccionados para comparar.
  const intentosSeleccionados = useMemo(() => {
    if (!datosExamen || intentosComparar.length < 2) return null
    return intentosComparar
      .map((i) => datosExamen.resultados[i])
      .filter(Boolean)
  }, [datosExamen, intentosComparar])

  // Ajusta el grid de cards en comparación para que no queden columnas vacías.
  const claseGridComparacion = useMemo(() => {
    const n = intentosSeleccionados?.length ?? 0
    if (n <= 1) return 'grid-cols-1'
    if (n === 2) return 'sm:grid-cols-2 lg:grid-cols-2'
    if (n === 3) return 'sm:grid-cols-2 lg:grid-cols-3'
    return 'sm:grid-cols-2 lg:grid-cols-4'
  }, [intentosSeleccionados?.length])

  return (
    <div className="space-y-6">
      {/* Selector de examen + intento en la misma fila */}
      <div className="flex flex-col gap-6">
        {/* Selector de examen */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground">
            Examen:
          </label>
          <div className="flex flex-wrap gap-2">
            {examenesUnicos.map((examenId) => (
              <button
                key={examenId}
                onClick={() => cargarExamen(examenId)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                  examenSeleccionado === examenId
                    ? 'bg-primary text-primary-foreground shadow-md'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Examen #{examenId}
              </button>
            ))}
          </div>
        </div>

        {/* Selector de intento + botón comparar (mismo fila) */}
        {datosExamen && !cargando && (
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm font-medium text-muted-foreground">
              Intento:
            </label>
            <div className="flex flex-wrap gap-2">
              {datosExamen.resultados.map((r, i) => (
                <button
                  key={r.id}
                  onClick={() => {
                    if (modoComparar) {
                      setIntentosComparar((prev) =>
                        prev.includes(i)
                          ? prev.filter((x) => x !== i)
                          : [...prev, i]
                      )
                    } else {
                      setIntentoIdx(i)
                    }
                  }}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                    modoComparar
                      ? intentosComparar.includes(i)
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                      : intentoIdx === i
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                  }`}
                >
                  #{i + 1} —{' '}
                  {new Date(r.completado_en).toLocaleDateString('es-CL')}
                </button>
              ))}
            </div>
            {datosExamen.resultados.length >= 2 && (
              <button
                onClick={() => {
                  setModoComparar(!modoComparar)
                  if (!modoComparar) {
                    setIntentosComparar([0, 1])
                  }
                }}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                  modoComparar
                    ? 'bg-primary text-primary-foreground shadow-md'
                    : 'border border-input bg-background text-muted-foreground hover:text-foreground'
                }`}
              >
                <GitCompareArrows className="h-4 w-4" />
                Comparar
              </button>
            )}
          </div>
        )}
      </div>

      {/* Estado de carga */}
      {cargando && (
        <div className="flex h-[40vh] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Sin examen seleccionado */}
      {!examenSeleccionado && !cargando && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Hash className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Selecciona un examen para ver tus resultados
          </p>
        </div>
      )}

      {/* Contenido del examen seleccionado */}
      {datosExamen && !cargando && (
        <>
          {/* Título del examen como encabezado de contexto */}
          <p className="text-sm text-muted-foreground">
            {datosExamen.examen_titulo}
          </p>

          {/* Vista de comparación */}
           {modoComparar &&
             intentosSeleccionados &&
             intentosSeleccionados.length >= 2 && (
               <>
                 {/* Cards completas por intento */}
                 <div className={cn('grid gap-4', claseGridComparacion)}>
                   {intentosSeleccionados.map((intento, idx) => (
                     <CardIntento
                       key={intento.id}
                       intento={intento}
                       indice={intentosComparar[idx]}
                      color={coloresIntentos[idx % coloresIntentos.length]}
                    />
                  ))}
                </div>

                {/* Gráficos agrupados */}
                <GraficosComparacion
                  intentosSeleccionados={intentosSeleccionados}
                  intentosComparar={intentosComparar}
                />
              </>
            )}

          {/* Vista de intento individual */}
           {!modoComparar && intentoActual && (
             <>
               {/* Card a ancho completo + gráficos debajo */}
               <div className="space-y-4">
                 <CardIntento
                   intento={intentoActual}
                   indice={intentoIdx}
                   color={coloresIntentos[0]}
                 />
                 <div className="grid gap-4 lg:grid-cols-2">
                   <GraficosIntento intento={intentoActual} />
                 </div>
               </div>

               {/* Tabla de respuestas */}
               <TablaRespuestas respuestas={intentoActual.respuestas} />
             </>
           )}
        </>
      )}
    </div>
  )
}
