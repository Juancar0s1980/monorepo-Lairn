// Página "Mi desempeño" del estudiante en Saber Pro (HU-23).
//
// Ruta /saber-pro/desempeno. El estudiante consulta su percentil frente al
// curso y, opcionalmente, frente a un simulacro concreto. La respuesta del
// backend solo contiene sus propios agregados: no hay nombres, correos ni
// posiciones de otros estudiantes (HU-23.4). La página lo comunica de forma
// explícita con una nota de privacidad.

import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  BarChart3,
  ClipboardList,
  GraduationCap,
  Lock,
  Loader2,
  Sparkles,
  Target,
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
import { useCursosEstudianteSaberPro } from '@/hooks/use-cursos-estudiante-saber-pro'
import { useDesempenoSaberPro } from '@/hooks/use-desempeno-saber-pro'
import { useSimulacrosEstudianteSaberPro } from '@/hooks/use-simulacros-estudiante-saber-pro'
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

function DatoDesempeno({
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

export default function PaginaDesempenoEstudianteSaberPro() {
  const navigate = useNavigate()
  const {
    inscripciones,
    cargando: cargandoCursos,
    error: errorCursos,
    recargar: recargarCursos,
  } = useCursosEstudianteSaberPro()
  const { simulacros, cargando: cargandoSimulacros } = useSimulacrosEstudianteSaberPro()
  const [cursoId, setCursoId] = useState<number | null>(null)
  const [simulacroId, setSimulacroId] = useState<number | null>(null)

  const cursos = useMemo(
    () => inscripciones.map((inscripcion) => inscripcion.curso),
    [inscripciones]
  )
  const cursoSeleccionado = cursos.find((curso) => curso.id === cursoId) ?? cursos[0] ?? null
  const simulacrosDelCurso = useMemo(
    () =>
      simulacros.filter(
        (simulacro) => simulacro.curso.id === (cursoSeleccionado?.id ?? -1)
      ),
    [cursoSeleccionado?.id, simulacros]
  )
  const simulacroSeleccionado =
    simulacrosDelCurso.find((simulacro) => simulacro.id === simulacroId) ?? null
  const simulacroEfectivo = simulacroSeleccionado?.id ?? null

  const { datos, cargando, error, recargar } = useDesempenoSaberPro(
    cursoSeleccionado?.id ?? null,
    simulacroEfectivo
  )

  const porcentaje = datos?.hay_comparacion ? (datos.percentil ?? 0) : 0

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
              Mi <span className="text-[#e8740e] dark:text-[#F29A52]">desempeño</span>
            </h1>
            <p className={cn('mt-2 max-w-2xl text-sm leading-relaxed', paletaSaberPro.texto)}>
              Compara tu resultado con el de tu curso. Solo verás tu percentil y tus propios
              datos: los nombres y posiciones de tus compañeros son privados.
            </p>
          </div>
          <span
            className={cn(
              'hidden h-16 w-16 items-center justify-center rounded-2xl sm:flex',
              paletaSaberPro.chipGold
            )}
          >
            <Target className="h-8 w-8" />
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
              Aún no tienes cursos Saber Pro
            </h2>
            <p className={cn('mt-2 max-w-md text-sm leading-relaxed', paletaSaberPro.texto)}>
              Únete con el código de tu docente para presentar simulacros y comparar tu
              desempeño con el grupo.
            </p>
            <Button
              type="button"
              className={cn('mt-5', paletaSaberPro.botonAccion)}
              onClick={() => navigate('/saber-pro')}
            >
              Ir al panel Saber Pro
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
                  <label htmlFor="desempeno-curso" className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
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
                    <SelectTrigger id="desempeno-curso" className={selectTriggerAncho}>
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
                  <label htmlFor="desempeno-simulacro" className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
                    Comparar con
                  </label>
                  <Select
                    items={[
                      { value: 'todos', label: 'Todo el curso (promedio por simulacro)' },
                      ...simulacrosDelCurso.map((simulacro) => ({
                        value: String(simulacro.id),
                        label: simulacro.titulo || `Simulacro #${simulacro.id}`,
                      })),
                    ]}
                    value={simulacroSeleccionado ? String(simulacroSeleccionado.id) : 'todos'}
                    onValueChange={(valor) => setSimulacroId(valor === 'todos' ? null : Number(valor))}
                  >
                    <SelectTrigger id="desempeno-simulacro" className={selectTriggerAncho}>
                      <SelectValue placeholder="Comparar con" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todos" className={selectItemLargo}>
                        Todo el curso (promedio por simulacro)
                      </SelectItem>
                      {simulacrosDelCurso.map((simulacro) => (
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

            {cargando && (
              <div
                className={cn(
                  'mt-6 flex min-h-40 flex-col items-center justify-center gap-3 rounded-2xl border',
                  paletaSaberPro.superficie,
                  paletaSaberPro.borde
                )}
              >
                <Loader2 className={cn('h-8 w-8 animate-spin', paletaSaberPro.accion)} />
                <p className={cn('text-sm', paletaSaberPro.texto)}>Calculando tu desempeño...</p>
              </div>
            )}

            {!cargando && error && (
              <div className="mt-6">
                <ErrorEstado mensaje={error} reintentar={() => void recargar()} />
              </div>
            )}

            {!cargando && !error && datos && (
              <>
                {!datos.tiene_resultados ? (
                  <section
                    className={cn(
                      'mt-6 flex flex-col items-center rounded-3xl border border-dashed p-10 text-center',
                      paletaSaberPro.bandaAlterna,
                      paletaSaberPro.borde
                    )}
                  >
                    <span className={cn('flex h-16 w-16 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
                      <ClipboardList className="h-8 w-8" />
                    </span>
                    <h2 className={cn('mt-4 text-lg font-bold', paletaSaberPro.titulo)}>
                      Aún no tienes resultados calificados
                    </h2>
                    <p className={cn('mt-2 max-w-md text-sm leading-relaxed', paletaSaberPro.texto)}>
                      {datos.mensaje}
                    </p>
                    <Button
                      type="button"
                      className={cn('mt-5 gap-2', paletaSaberPro.botonAccion)}
                      onClick={() => navigate('/saber-pro/simulacros')}
                    >
                      <Sparkles className="h-4 w-4" /> Ir a mis simulacros
                    </Button>
                  </section>
                ) : (
                  <>
                    <section
                      className={cn(
                        'relative mt-6 overflow-hidden rounded-3xl border p-6 md:p-8',
                        paletaSaberPro.bandaProfunda,
                        paletaSaberPro.borde
                      )}
                    >
                      <div
                        aria-hidden="true"
                        className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-radial from-[#c89b14]/20 to-transparent dark:from-[#E3C063]/15"
                      />
                      <div className="relative grid gap-8 lg:grid-cols-[auto_1fr] lg:items-center">
                        <div className="text-center lg:text-left">
                          <p className={cn('text-[11px] font-semibold uppercase tracking-[0.18em]', paletaSaberPro.apoyoTitulo)}>
                            Percentil del curso
                          </p>
                          <p
                            className={cn(
                              'mt-1 text-[clamp(3.25rem,8vw,5rem)] font-black leading-none',
                              paletaSaberPro.titulo
                            )}
                          >
                            {datos.hay_comparacion ? `${datos.percentil}%` : '—'}
                          </p>
                          <p className={cn('mt-1 text-xs', paletaSaberPro.apoyo)}>
                            {datos.hay_comparacion
                              ? 'de estudiantes superados'
                              : 'sin comparación todavía'}
                          </p>
                        </div>

                        <div>
                          <div className={cn('h-4 overflow-hidden rounded-full', paletaSaberPro.esqueleto)}>
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-[#1e3a5f] via-[#c89b14] to-[#e8740e] transition-[width] duration-700 dark:from-[#F3EDE1] dark:via-[#E3C063] dark:to-[#F29A52]"
                              style={{ width: `${porcentaje}%` }}
                              aria-hidden="true"
                            />
                          </div>
                          <p className={cn('mt-4 text-sm leading-relaxed', paletaSaberPro.texto)}>
                            {datos.mensaje}
                          </p>
                          <div className="mt-4 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                              {datos.total_estudiantes} estudiante
                              {datos.total_estudiantes === 1 ? '' : 's'} con resultados
                            </Badge>
                            <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                              {datos.filtro.tipo === 'simulacro' ? 'Simulacro' : 'Área del curso'}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </section>

                    <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
                      <DatoDesempeno
                        icono={<Trophy className="h-3 w-3" />}
                        etiqueta="Mi calificación"
                        valor={
                          datos.mi_calificacion === null ? '—' : datos.mi_calificacion.toFixed(2)
                        }
                        detalle="sobre 5.00"
                      />
                      <DatoDesempeno
                        icono={<BarChart3 className="h-3 w-3" />}
                        etiqueta="Mi puntaje"
                        valor={datos.mi_puntaje === null ? '—' : `${datos.mi_puntaje.toFixed(1)}%`}
                        detalle="aciertos del intento"
                      />
                      <DatoDesempeno
                        icono={<Users className="h-3 w-3" />}
                        etiqueta="Comparado con"
                        valor={String(datos.total_estudiantes)}
                        detalle="estudiantes con resultados"
                      />
                      <DatoDesempeno
                        icono={<Target className="h-3 w-3" />}
                        etiqueta="Intentos"
                        valor={String(datos.mis_intentos_considerados)}
                        detalle={`${datos.mis_simulacros_considerados} simulacro${
                          datos.mis_simulacros_considerados === 1 ? '' : 's'
                        }`}
                      />
                    </div>

                    <div
                      className={cn(
                        'mt-5 flex items-start gap-3 rounded-2xl border p-4',
                        paletaSaberPro.superficie,
                        paletaSaberPro.borde
                      )}
                    >
                      <span
                        className={cn(
                          'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
                          paletaSaberPro.iconoChip
                        )}
                      >
                        <Lock className="h-5 w-5" />
                      </span>
                      <div>
                        <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>
                          Comparación privada
                        </p>
                        <p className={cn('mt-1 text-xs leading-relaxed', paletaSaberPro.texto)}>
                          Tu percentil se calcula con los resultados de tu curso, pero solo ves tus
                          propios datos. Los nombres, correos y posiciones de tus compañeros no se
                          muestran en esta vista.
                        </p>
                      </div>
                    </div>

                    <p className={cn('mt-3 text-[11px] leading-relaxed', paletaSaberPro.apoyo)}>
                      Solo se consideran intentos finalizados y calificados. Al comparar todo el
                      curso se promedia el mejor intento de cada simulacro para no favorecer a
                      quien repite más veces.
                    </p>
                  </>
                )}
              </>
            )}
          </main>
        )}
      </div>
    </div>
  )
}
