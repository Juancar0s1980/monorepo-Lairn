// Panel de Redes Neuronales (solo Administrador).
// Muestra el estado de los modelos de Knowledge Tracing (métricas AUC/accuracy/
// F1/RMSE) y los resultados agregados del sistema: distribución de niveles de
// dominio, desglose por concepto y por profesor.
// Datos de:
//   GET /analitica/administracion/redes/modelos/
//   GET /analitica/administracion/redes/resultados/

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { CardStat } from '@/components/card-stat'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Activity,
  AlertCircle,
  BrainCircuit,
  GraduationCap,
  Layers,
  Target,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import type { RedesModelos, RedesResultados, ResumenNiveles } from '@/types/redes'

function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="h-8 w-16 rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  )
}

// Formatea una probabilidad/métrica 0..1 como porcentaje.
function pct(x: number | null | undefined): string {
  return x == null ? '—' : `${(x * 100).toFixed(1)}%`
}

// Barra de progreso simple (valor 0..1) para una métrica.
function BarraMetrica({ label, valor }: { label: string; valor: number | null }) {
  const ancho = valor == null ? 0 : Math.max(0, Math.min(1, valor)) * 100
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span className="font-medium text-foreground">{pct(valor)}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${ancho}%` }} />
      </div>
    </div>
  )
}

// Barra apilada de distribución de niveles (débil / desarrollo / dominado).
function BarraNiveles({ resumen }: { resumen: ResumenNiveles }) {
  const d = resumen.distribucion_niveles
  const total = d.debil + d.desarrollo + d.dominado
  const w = (n: number) => (total ? (n / total) * 100 : 0)
  if (total === 0) {
    return <p className="text-xs text-muted-foreground">Sin conceptos evaluados aún</p>
  }
  return (
    <div className="space-y-2">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full bg-destructive" style={{ width: `${w(d.debil)}%` }} />
        <div className="h-full bg-amber-500" style={{ width: `${w(d.desarrollo)}%` }} />
        <div className="h-full bg-emerald-500" style={{ width: `${w(d.dominado)}%` }} />
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-destructive" /> Débil: {d.debil}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-500" /> En desarrollo: {d.desarrollo}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500" /> Dominado: {d.dominado}
        </span>
      </div>
    </div>
  )
}

// Badge de nivel promedio (1 débil, 2 desarrollo, 3 dominado).
function NivelBadge({ nivel }: { nivel: number | null }) {
  if (nivel == null) return <span className="text-muted-foreground">—</span>
  const variante = nivel >= 2.5 ? 'default' : nivel >= 1.5 ? 'secondary' : 'destructive'
  return <Badge variant={variante}>{nivel.toFixed(2)}</Badge>
}

export default function PaginaRedesAdmin() {
  const [modelos, setModelos] = useState<RedesModelos | null>(null)
  const [resultados, setResultados] = useState<RedesResultados | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const cargar = async () => {
      try {
        const [resModelos, resResultados] = await Promise.all([
          api.get<RedesModelos>('/analitica/administracion/redes/modelos/'),
          api.get<RedesResultados>('/analitica/administracion/redes/resultados/'),
        ])
        setModelos(resModelos.data)
        setResultados(resResultados.data)
      } catch {
        setError('No se pudo cargar el panel de redes neuronales')
        toast.error('No se pudo cargar el panel de redes neuronales')
      } finally {
        setCargando(false)
      }
    }
    cargar()
  }, [])

  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-2">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-4 w-48 rounded bg-muted" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <SkeletonCard className="h-64" />
      </div>
    )
  }

  if (error || !resultados) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {error ?? 'No se pudo cargar el panel'}
        </p>
      </div>
    )
  }

  const lista = modelos?.modelos ?? []
  const mlDisponible = modelos?.disponible ?? false
  const mejorAuc = lista.reduce<number | null>(
    (max, m) => (m.metricas.auc != null && (max == null || m.metricas.auc > max) ? m.metricas.auc : max),
    null,
  )
  const g = resultados.global

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Redes Neuronales</h2>
        <p className="text-muted-foreground">
          Estado de los modelos de Knowledge Tracing y resultados de dominio del sistema
        </p>
      </div>

      {/* Stats generales */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <CardStat
          titulo="Modelos entrenados"
          valor={lista.length}
          icono={BrainCircuit}
          variante="primary"
          subtitulo={modelos?.modelo_activo ? `Activo: ${modelos.modelo_activo}` : 'Sin modelo activo'}
        />
        <CardStat
          titulo="Mejor AUC"
          valor={pct(mejorAuc)}
          icono={Activity}
          variante="exito"
          subtitulo="Área bajo la curva ROC"
        />
        <CardStat
          titulo="Estudiantes evaluados"
          valor={g.estudiantes}
          icono={Users}
          subtitulo={`${g.conceptos_evaluados} conceptos evaluados`}
        />
        <CardStat
          titulo="Dominio promedio"
          valor={pct(g.p_dominado_promedio)}
          icono={Target}
          subtitulo={g.nivel_promedio != null ? `Nivel medio ${g.nivel_promedio.toFixed(2)}/3` : 'Sin datos'}
        />
      </div>

      {/* Estado de los modelos */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Estado de los modelos</h3>

        {!mlDisponible && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            El microservicio de ML no está disponible. Se muestran solo los resultados agregados.
          </div>
        )}

        {mlDisponible && (
          <div className="grid gap-4 md:grid-cols-2">
            {lista.map((m) => (
              <Card key={m.nombre}>
                <CardContent className="space-y-4 p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="flex items-center gap-2 font-semibold">
                        <BrainCircuit className="h-4 w-4 text-primary shrink-0" />
                        <span className="truncate">{m.nombre}</span>
                        {m.activo && <Badge>Activo</Badge>}
                      </p>
                      <p className="text-xs text-muted-foreground">{m.tipo}</p>
                    </div>
                    <div className="text-right text-xs text-muted-foreground shrink-0">
                      {m.fuente && <p className="capitalize">{m.fuente}</p>}
                      {m.n_estudiantes != null && <p>{m.n_estudiantes} estud.</p>}
                      {m.n_skills != null && <p>{m.n_skills} skills</p>}
                    </div>
                  </div>
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    <BarraMetrica label="AUC" valor={m.metricas.auc} />
                    <BarraMetrica label="Accuracy" valor={m.metricas.accuracy} />
                    <BarraMetrica label="F1" valor={m.metricas.f1} />
                    <BarraMetrica label="RMSE" valor={m.metricas.rmse} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Resultados globales */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Distribución de dominio (global)</h3>
        <Card>
          <CardContent className="p-5">
            <BarraNiveles resumen={g} />
          </CardContent>
        </Card>
      </div>

      {/* Conceptos */}
      <div className="space-y-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          <Layers className="h-4 w-4 text-muted-foreground" /> Dominio por concepto
        </h3>
        {resultados.conceptos.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <Layers className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              Aún no hay conceptos evaluados
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Concepto</TableHead>
                <TableHead>Evaluaciones</TableHead>
                <TableHead>Nivel promedio</TableHead>
                <TableHead className="hidden sm:table-cell">P(dominado)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {resultados.conceptos.map((c) => (
                <TableRow key={c.concepto}>
                  <TableCell className="font-medium">{c.concepto}</TableCell>
                  <TableCell>{c.evaluaciones}</TableCell>
                  <TableCell><NivelBadge nivel={c.nivel_promedio} /></TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">
                    {pct(c.p_dominado_promedio)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Por profesor */}
      <div className="space-y-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          <GraduationCap className="h-4 w-4 text-muted-foreground" /> Resultados por profesor
        </h3>
        {resultados.por_profesor.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <GraduationCap className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              Aún no hay resultados por profesor
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Profesor</TableHead>
                <TableHead>Estudiantes</TableHead>
                <TableHead className="hidden sm:table-cell">Conceptos</TableHead>
                <TableHead>Nivel prom.</TableHead>
                <TableHead className="hidden md:table-cell">P(dominado)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {resultados.por_profesor.map((p) => (
                <TableRow key={p.profesor}>
                  <TableCell className="font-medium">{p.profesor}</TableCell>
                  <TableCell>{p.estudiantes}</TableCell>
                  <TableCell className="hidden sm:table-cell">{p.conceptos_evaluados}</TableCell>
                  <TableCell><NivelBadge nivel={p.nivel_promedio} /></TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground">
                    {pct(p.p_dominado_promedio)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
