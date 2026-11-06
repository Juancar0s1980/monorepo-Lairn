// Página de ranking de un curso Saber Pro para el docente (HU-23).
//
// Ruta /saber-pro/ranking. El docente propietario consulta el listado nominal
// de sus estudiantes, ordenado por desempeño. Puede comparar todo el curso
// (promedio del mejor intento de cada simulacro) o un simulacro concreto.
// La vista es la única del módulo que muestra nombres y correos de estudiantes;
// los datos son exclusivamente de los cursos del docente autenticado.

import { useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  Award,
  BarChart3,
  Crown,
  GraduationCap,
  Loader2,
  Medal,
  Trophy,
  Users,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { useRankingSaberPro } from '@/hooks/use-ranking-saber-pro'
import { useSimulacrosSaberPro } from '@/hooks/use-simulacros-saber-pro'
import type { FilaRankingSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import {
  paletaSaberPro,
  selectContenidoAncho,
  selectItemLargo,
  selectTriggerAncho,
} from './utilidades'

function ErrorEstado({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-2xl border p-12 text-center',
        paletaSaberPro.superficie,
        paletaSaberPro.borde
      )}
    >
      <span className={cn('flex h-12 w-12 items-center justify-center rounded-full', paletaSaberPro.chipAccion)}>
        <AlertCircle className="h-6 w-6" />
      </span>
      <p className={cn('mt-4 text-sm font-medium', paletaSaberPro.titulo)}>{mensaje}</p>
      <Button type="button" className={cn('mt-4', paletaSaberPro.botonNeutro)} onClick={reintentar}>
        Reintentar
      </Button>
    </div>
  )
}

function DatoResumen({
  icono,
  etiqueta,
  valor,
  detalle,
}: {
  icono: ReactNode
  etiqueta: string
  valor: string
  detalle: string
}) {
  return (
    <div className={cn('rounded-xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <p className={cn('flex items-center gap-1.5 text-[10px] uppercase tracking-[0.08em]', paletaSaberPro.apoyo)}>
        {icono} {etiqueta}
      </p>
      <p className={cn('mt-1 text-2xl font-black', paletaSaberPro.titulo)}>{valor}</p>
      <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>{detalle}</p>
    </div>
  )
}

function IconoPosicion({ posicion }: { posicion: number }) {
  if (posicion === 1) return <Crown className="h-4 w-4 text-[#c89b14] dark:text-[#E3C063]" />
  if (posicion === 2) return <Medal className="h-4 w-4 text-[#1e3a5f] dark:text-[#F5EFE0]" />
  if (posicion === 3) return <Award className="h-4 w-4 text-[#e8740e] dark:text-[#F29A52]" />
  return null
}

function FilaRanking({ fila }: { fila: FilaRankingSaberPro }) {
  const destacado = fila.posicion <= 3
  return (
    <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
      <TableCell className="w-16 py-3 text-center">
        <span
          className={cn(
            'inline-flex h-8 min-w-8 items-center justify-center gap-1 rounded-full px-2 text-sm font-bold',
            destacado
              ? paletaSaberPro.numeracionPaso
              : cn('bg-transparent', paletaSaberPro.texto)
          )}
        >
          <IconoPosicion posicion={fila.posicion} />
          {fila.posicion}
        </span>
      </TableCell>
      <TableCell className="min-w-52 py-3">
        <p className={cn('font-semibold', paletaSaberPro.titulo)}>
          {fila.estudiante.nombre_completo || 'Estudiante sin nombre'}
        </p>
        <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>{fila.estudiante.email}</p>
      </TableCell>
      <TableCell className={cn('py-3 text-center text-sm font-semibold', paletaSaberPro.texto)}>
        {fila.puntaje.toFixed(1)}%
      </TableCell>
      <TableCell className="py-3 text-center">
        <p
          className={cn(
            'text-lg font-black',
            fila.calificacion >= 3
              ? 'text-[#1e3a5f] dark:text-[#E3C063]'
              : 'text-[#b8432a] dark:text-[#F29A52]'
          )}
        >
          {fila.calificacion.toFixed(2)}
        </p>
        <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>/ 5.00</p>
      </TableCell>
      <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
        {fila.intentos_considerados}
      </TableCell>
      <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
        {fila.simulacros_considerados}
      </TableCell>
    </TableRow>
  )
}

export default function PaginaRankingSaberPro() {
  const navigate = useNavigate()
  const {
    cursos,
    cargando: cargandoCursos,
    error: errorCursos,
    recargar: recargarCursos,
  } = useCursosSaberPro()
  const [cursoId, setCursoId] = useState<number | null>(null)
  const [simulacroId, setSimulacroId] = useState<number | null>(null)

  const cursoSeleccionado = cursos.find((curso) => curso.id === cursoId) ?? cursos[0] ?? null
  const { simulacros, cargando: cargandoSimulacros } = useSimulacrosSaberPro(
    cursoSeleccionado?.id ?? null
  )
  const { datos, cargando, error, recargar } = useRankingSaberPro(
    cursoSeleccionado?.id ?? null,
    simulacroId
  )

  const promedio =
    datos && datos.ranking.length > 0
      ? datos.ranking.reduce((total, fila) => total + fila.calificacion, 0) / datos.ranking.length
      : 0
  const lider = datos?.ranking[0] ?? null
  const simulacroSeleccionado = simulacros.find((simulacro) => simulacro.id === simulacroId) ?? null

  return (
    <div className={cn('relative overflow-hidden rounded-2xl', paletaSaberPro.banda)}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={cn('h-2 w-full', paletaSaberPro.franja)} />

      <div className="relative p-6 md:p-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button
              type="button"
              onClick={() => navigate('/saber-pro')}
              className={cn(
                'inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em]',
                paletaSaberPro.accion
              )}
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Volver al panel
            </button>
            <h1
              className={cn(
                'mt-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight',
                paletaSaberPro.fuenteHero,
                paletaSaberPro.titulo
              )}
            >
              Ranking <span className="text-[#e8740e] dark:text-[#F29A52]">Saber Pro</span>
            </h1>
            <p className={cn('mt-2 max-w-2xl text-sm leading-relaxed', paletaSaberPro.texto)}>
              Consulta el desempeño de tus estudiantes por simulacro o por el área del curso.
              Los nombres solo están visibles para ti como docente del curso.
            </p>
          </div>
          <span
            className={cn(
              'hidden h-16 w-16 items-center justify-center rounded-2xl sm:flex',
              paletaSaberPro.chipGold
            )}
          >
            <Trophy className="h-8 w-8" />
          </span>
        </header>

        {cargandoCursos && (
          <div className={cn('mt-8 flex items-center gap-2 text-sm', paletaSaberPro.apoyo)}>
            <Loader2 className="h-4 w-4 animate-spin" /> Cargando tus cursos...
          </div>
        )}

        {!cargandoCursos && errorCursos && (
          <div className="mt-8">
            <ErrorEstado mensaje={errorCursos} reintentar={() => void recargarCursos()} />
          </div>
        )}

        {!cargandoCursos && !errorCursos && cursos.length === 0 && (
          <section
            className={cn(
              'mt-8 flex flex-col items-center rounded-3xl border border-dashed p-12 text-center',
              paletaSaberPro.bandaAlterna,
              paletaSaberPro.borde
            )}
          >
            <span className={cn('flex h-16 w-16 items-center justify-center rounded-full', paletaSaberPro.chipAccion)}>
              <GraduationCap className="h-8 w-8" />
            </span>
            <h2 className={cn('mt-4 text-lg font-bold', paletaSaberPro.titulo)}>
              Necesitas un curso primero
            </h2>
            <p className={cn('mt-2 max-w-md text-sm leading-relaxed', paletaSaberPro.texto)}>
              El ranking se calcula con los resultados de los simulacros de cada curso Saber Pro.
              Crea tu primer curso y vuelve a esta sección.
            </p>
            <Button
              type="button"
              className={cn('mt-5 gap-2', paletaSaberPro.botonAccion)}
              onClick={() => navigate('/saber-pro/cursos')}
            >
              Crear curso
            </Button>
          </section>
        )}

        {!cargandoCursos && !errorCursos && cursoSeleccionado && (
          <main className="mt-8">
            <section
              className={cn('rounded-2xl border p-4 md:p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}
            >
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-1.5">
                  <label htmlFor="ranking-curso" className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
                    Curso Saber Pro
                  </label>
                  <Select
                    items={cursos.map((curso) => ({
                      value: String(curso.id),
                      label: `${curso.nombre} - ${curso.area.nombre}`,
                    }))}
                    value={String(cursoSeleccionado.id)}
                    onValueChange={(valor) => {
                      setCursoId(Number(valor))
                      setSimulacroId(null)
                    }}
                  >
                    <SelectTrigger id="ranking-curso" className={selectTriggerAncho}>
                      <SelectValue placeholder="Selecciona un curso" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      {cursos.map((curso) => (
                        <SelectItem key={curso.id} value={String(curso.id)} className={selectItemLargo}>
                          {curso.nombre} - {curso.area.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="ranking-simulacro" className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
                    Filtro de comparación
                  </label>
                  <Select
                    items={[
                      { value: 'todos', label: 'Todo el curso (promedio por simulacro)' },
                      ...simulacros.map((simulacro) => ({
                        value: String(simulacro.id),
                        label: simulacro.titulo || `Simulacro #${simulacro.id}`,
                      })),
                    ]}
                    value={simulacroId === null ? 'todos' : String(simulacroId)}
                    onValueChange={(valor) => setSimulacroId(valor === 'todos' ? null : Number(valor))}
                  >
                    <SelectTrigger id="ranking-simulacro" className={selectTriggerAncho}>
                      <SelectValue placeholder="Filtro de comparación" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todos" className={selectItemLargo}>
                        Todo el curso (promedio por simulacro)
                      </SelectItem>
                      {simulacros.map((simulacro) => (
                        <SelectItem
                          key={simulacro.id}
                          value={String(simulacro.id)}
                          className={selectItemLargo}
                        >
                          {simulacro.titulo || `Simulacro #${simulacro.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {cargandoSimulacros && (
                    <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>Cargando simulacros...</p>
                  )}
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {cursoSeleccionado.area.nombre}
                </Badge>
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {simulacroSeleccionado ? 'Simulacro específico' : 'Todo el curso'}
                </Badge>
              </div>
            </section>

            <section aria-labelledby="tabla-ranking" className="mt-6">
              <div className="flex items-center gap-3">
                <span className={cn('h-6 w-1.5 rounded-full', paletaSaberPro.separador)} aria-hidden="true" />
                <div>
                  <p className={cn('text-[11px] font-semibold uppercase tracking-[0.2em]', paletaSaberPro.apoyoTitulo)}>
                    Desempeño del grupo
                  </p>
                  <h2
                    id="tabla-ranking"
                    className={cn('mt-0.5 text-[22px] font-bold tracking-tight', paletaSaberPro.titulo)}
                  >
                    Listado nominal
                  </h2>
                </div>
              </div>

              {cargando && (
                <div
                  className={cn(
                    'mt-5 flex min-h-40 flex-col items-center justify-center gap-3 rounded-2xl border',
                    paletaSaberPro.superficie,
                    paletaSaberPro.borde
                  )}
                >
                  <Loader2 className={cn('h-8 w-8 animate-spin', paletaSaberPro.accion)} />
                  <p className={cn('text-sm', paletaSaberPro.texto)}>Calculando ranking...</p>
                </div>
              )}

              {!cargando && error && (
                <div className="mt-5">
                  <ErrorEstado mensaje={error} reintentar={() => void recargar()} />
                </div>
              )}

              {!cargando && !error && datos && (
                <>
                  <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
                    <DatoResumen
                      icono={<Users className="h-3 w-3" />}
                      etiqueta="Con resultados"
                      valor={String(datos.total_estudiantes)}
                      detalle={`de ${datos.total_inscritos} inscritos`}
                    />
                    <DatoResumen
                      icono={<BarChart3 className="h-3 w-3" />}
                      etiqueta="Promedio"
                      valor={promedio.toFixed(2)}
                      detalle="calificación del grupo"
                    />
                    <DatoResumen
                      icono={<Trophy className="h-3 w-3" />}
                      etiqueta="Líder"
                      valor={lider ? lider.calificacion.toFixed(2) : '—'}
                      detalle={lider?.estudiante.nombre_completo ?? 'sin resultados'}
                    />
                    <DatoResumen
                      icono={<GraduationCap className="h-3 w-3" />}
                      etiqueta="Filtro"
                      valor={simulacroSeleccionado ? 'Simulacro' : 'Curso'}
                      detalle={simulacroSeleccionado ? 'mejor intento' : 'promedio por simulacro'}
                    />
                  </div>

                  {datos.ranking.length === 0 ? (
                    <div
                      className={cn(
                        'mt-5 flex flex-col items-center rounded-2xl border border-dashed p-10 text-center',
                        paletaSaberPro.bandaAlterna,
                        paletaSaberPro.borde
                      )}
                    >
                      <span className={cn('flex h-14 w-14 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
                        <Trophy className="h-7 w-7" />
                      </span>
                      <p className={cn('mt-3 text-base font-bold', paletaSaberPro.titulo)}>
                        Aún no hay resultados para comparar
                      </p>
                      <p className={cn('mt-1 max-w-md text-sm', paletaSaberPro.texto)}>
                        El ranking aparecerá cuando tus estudiantes finalicen simulacros y sus
                        intentos estén calificados.
                      </p>
                    </div>
                  ) : (
                    <div
                      className={cn(
                        'mt-5 overflow-x-auto rounded-2xl border',
                        paletaSaberPro.superficie,
                        paletaSaberPro.borde
                      )}
                    >
                      <Table className="bg-transparent [&_td]:text-[#2c3e50] dark:[&_td]:text-[#CFC9BA]">
                        <TableHeader>
                          <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
                            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Posición</TableHead>
                            <TableHead className={paletaSaberPro.apoyoTitulo}>Estudiante</TableHead>
                            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Puntaje</TableHead>
                            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Calificación</TableHead>
                            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Intentos</TableHead>
                            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Simulacros</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {datos.ranking.map((fila) => (
                            <FilaRanking key={fila.estudiante.id} fila={fila} />
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                  <p className={cn('mt-3 text-[11px] leading-relaxed', paletaSaberPro.apoyo)}>
                    Solo se consideran intentos finalizados y calificados. Al comparar todo el
                    curso se promedia el mejor intento de cada simulacro por estudiante para no
                    favorecer a quien repite más veces.
                  </p>
                </>
              )}
            </section>
          </main>
        )}
      </div>
    </div>
  )
}
