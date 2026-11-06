// Pestaña "Desempeño por RA" (HU-09.1, solo Administrador): porcentaje de
// acierto por resultado de aprendizaje, grupal (RA más débiles primero) e
// individual (estudiante × RA), filtrable por momento y evaluación.
// La métrica es provisional hasta validarla con Vicerrectoría (lo indica la UI).

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Info, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Academico } from '../use-academico'
import { mensajeError } from '../academico-utils'

interface CeldaRA {
  aciertos: number
  presentadas: number
  porcentaje: number | null
}

interface DesempenoRA {
  resumen: { evaluaciones: number; intentos: number; estudiantes: number }
  grupal: (CeldaRA & { resultado_id: number; descripcion: string; competencia: string; asignatura: string; estudiantes: number })[]
  individual: { estudiante: { id: number; nombre: string; email: string }; por_ra: Record<string, CeldaRA>; porcentaje_total: number | null }[]
  filtros: { momentos: { id: number; nombre: string }[]; evaluaciones: { id: number; nombre: string; momento_id: number }[] }
  metrica: string
}

const TODOS = 'todos'

function Barra({ valor }: { valor: number | null }) {
  if (valor === null) return <span className="text-muted-foreground">—</span>
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-muted" aria-hidden>
        <div className="h-full rounded-full bg-primary" style={{ width: `${valor}%` }} />
      </div>
      <span className="text-sm font-medium tabular-nums">{valor}%</span>
    </div>
  )
}

export function TabDesempenoRA({ ac }: { ac: Academico }) {
  const [momento, setMomento] = useState(TODOS)
  const [evaluacion, setEvaluacion] = useState(TODOS)
  const [datos, setDatos] = useState<DesempenoRA | null>(null)
  const [error, setError] = useState('')
  // Clave de la última consulta respondida: hay carga mientras no coincide con la actual.
  const clave = `${ac.programaId}|${momento}|${evaluacion}`
  const [claveCargada, setClaveCargada] = useState('')
  const cargando = !!ac.programaId && claveCargada !== clave

  useEffect(() => {
    if (!ac.programaId) return
    let activo = true
    const cargar = async () => {
      try {
        const params = new URLSearchParams()
        if (momento !== TODOS) params.set('momento', momento)
        if (evaluacion !== TODOS) params.set('evaluacion', evaluacion)
        const res = await api.get<DesempenoRA>(`/evaluacion/programas/${ac.programaId}/desempeno-ra/?${params}`)
        if (activo) {
          setDatos(res.data)
          setError('')
        }
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se pudo cargar el desempeño por RA.'))
      } finally {
        if (activo) setClaveCargada(`${ac.programaId}|${momento}|${evaluacion}`)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [ac.programaId, momento, evaluacion])

  const evaluacionesFiltradas = (datos?.filtros.evaluaciones ?? []).filter(
    (e) => momento === TODOS || String(e.momento_id) === momento,
  )
  const ras = datos?.grupal ?? []

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-3 space-y-0 md:flex-row md:items-end md:justify-between">
          <div>
            <CardTitle>Porcentaje de acierto por resultado de aprendizaje</CardTitle>
            <CardDescription>
              {datos
                ? `${datos.resumen.estudiantes} estudiante(s) · ${datos.resumen.intentos} evaluación(es) presentadas`
                : 'Resultados de las evaluaciones formales del programa'}
            </CardDescription>
          </div>
          <div className="flex w-full flex-col gap-2 sm:flex-row md:w-auto">
            <Select
              value={momento}
              onValueChange={(v) => {
                setMomento(v ?? TODOS)
                setEvaluacion(TODOS)
              }}
              items={[{ value: TODOS, label: 'Todos los momentos' }, ...(datos?.filtros.momentos ?? []).map((m) => ({ value: String(m.id), label: m.nombre }))]}
            >
              <SelectTrigger className="w-full sm:w-[200px]" aria-label="Filtrar por momento">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos los momentos</SelectItem>
                {(datos?.filtros.momentos ?? []).map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>{m.nombre}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={evaluacion}
              onValueChange={(v) => setEvaluacion(v ?? TODOS)}
              items={[{ value: TODOS, label: 'Todas las evaluaciones' }, ...evaluacionesFiltradas.map((e) => ({ value: String(e.id), label: e.nombre }))]}
            >
              <SelectTrigger className="w-full sm:w-[240px]" aria-label="Filtrar por evaluación">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todas las evaluaciones</SelectItem>
                {evaluacionesFiltradas.map((e) => (
                  <SelectItem key={e.id} value={String(e.id)}>{e.nombre}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {datos?.metrica && (
            <p className="flex items-start gap-2 rounded-lg bg-muted p-3 text-xs text-muted-foreground">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              Métrica {datos.metrica.charAt(0).toLowerCase() + datos.metrica.slice(1)}
            </p>
          )}
          {cargando ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
            </div>
          ) : error ? (
            <p role="alert" className="text-sm text-destructive">{error}</p>
          ) : !ras.length ? (
            <p className="text-sm text-muted-foreground">
              Aún no hay evaluaciones formales presentadas para este filtro. Los porcentajes aparecen cuando los
              estudiantes envían sus evaluaciones.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Resultado de aprendizaje</TableHead>
                  <TableHead className="hidden md:table-cell">Competencia</TableHead>
                  <TableHead>Acierto grupal</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Respuestas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ras.map((r) => (
                  <TableRow key={r.resultado_id}>
                    <TableCell className="whitespace-normal">
                      <span className="block font-medium">{r.descripcion}</span>
                      <span className="block text-xs text-muted-foreground">{r.asignatura} · {r.estudiantes} estudiante(s)</span>
                    </TableCell>
                    <TableCell className="hidden whitespace-normal text-sm md:table-cell">{r.competencia}</TableCell>
                    <TableCell><Barra valor={r.porcentaje} /></TableCell>
                    <TableCell className="hidden text-right text-xs text-muted-foreground sm:table-cell">
                      {r.aciertos} de {r.presentadas}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {!cargando && !error && ras.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Por estudiante</CardTitle>
            <CardDescription>Porcentaje de acierto de cada estudiante en cada RA evaluado.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Estudiante</TableHead>
                  {ras.map((r, i) => (
                    <TableHead key={r.resultado_id} className="text-center" title={r.descripcion}>
                      RA {i + 1}
                    </TableHead>
                  ))}
                  <TableHead className="text-center">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datos?.individual.map((f) => (
                  <TableRow key={f.estudiante.id}>
                    <TableCell>
                      <span className="block font-medium">{f.estudiante.nombre}</span>
                      <span className="block text-xs text-muted-foreground">{f.estudiante.email}</span>
                    </TableCell>
                    {ras.map((r) => {
                      const celda = f.por_ra[String(r.resultado_id)]
                      return (
                        <TableCell
                          key={r.resultado_id}
                          className={cn('text-center tabular-nums', celda?.porcentaje === null || !celda ? 'text-muted-foreground' : '')}
                          title={celda ? `${celda.aciertos} de ${celda.presentadas}` : 'Sin preguntas de este RA'}
                        >
                          {celda?.porcentaje ?? '—'}{celda && celda.porcentaje !== null ? '%' : ''}
                        </TableCell>
                      )
                    })}
                    <TableCell className="text-center font-medium tabular-nums">
                      {f.porcentaje_total === null ? '—' : `${f.porcentaje_total}%`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <ol className="mt-3 space-y-0.5 text-xs text-muted-foreground">
              {ras.map((r, i) => (
                <li key={r.resultado_id}>RA {i + 1}: {r.descripcion}</li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
