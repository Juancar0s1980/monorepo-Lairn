// Pagina de simulacros disponibles del estudiante (HU-19.5).
//
// Ruta /saber-pro/simulacros. Solo lista simulacros activos de cursos activos a
// los que el estudiante esta inscrito; el backend no expone preguntas ni
// respuestas. El boton de inicio navega a la presentacion cronometrada de la
// HU-21, que inicia o reanuda el intento en el servidor.
//
// Identidad institucional del modulo: banda beige/navy, franja navy-dorado-
// naranja, hero en Montserrat y tarjetas Shadcn sobre superficie.

import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  ClipboardList,
  Clock,
  GraduationCap,
  ListChecks,
  Play,
  Repeat,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSimulacrosEstudianteSaberPro } from '@/hooks/use-simulacros-estudiante-saber-pro'
import { solicitarPantallaCompleta } from '@/utilities/pantalla-completa'
import type { SimulacroEstudianteSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerAncho } from './utilidades'

function SkeletonSimulacros() {
  return (
    <div aria-busy="true" aria-label="Cargando simulacros disponibles" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 3 }).map((_, indice) => (
        <div
          key={indice}
          className={`h-64 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-10 w-10 rounded-xl ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-4 w-2/3 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-14 w-full rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

function ErrorEstado({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-2xl border p-12 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
        <AlertCircle className="h-6 w-6" />
      </span>
      <p className={`mt-4 text-sm font-medium ${paletaSaberPro.titulo}`}>{mensaje}</p>
      <Button type="button" className={`mt-4 ${paletaSaberPro.botonNeutro}`} onClick={reintentar}>
        Reintentar
      </Button>
    </div>
  )
}

function Dato({ icono, etiqueta, valor }: { icono: ReactNode; etiqueta: string; valor: string }) {
  return (
    <div className="rounded-lg bg-[#f3ede1]/70 px-2 py-1.5 dark:bg-[#172A45]/70">
      <p className={`flex items-center gap-1 text-[9px] uppercase tracking-[0.08em] ${paletaSaberPro.apoyo}`}>
        {icono} {etiqueta}
      </p>
      <p className={`mt-0.5 truncate text-[11px] font-semibold ${paletaSaberPro.titulo}`}>{valor}</p>
    </div>
  )
}

function TarjetaSimulacroEstudiante({
  simulacro,
  onIniciar,
}: {
  simulacro: SimulacroEstudianteSaberPro
  onIniciar: (simulacro: SimulacroEstudianteSaberPro) => void
}) {
  const enProgreso = simulacro.intento_en_progreso
  const vencido = simulacro.vencido
  const bloqueado = !simulacro.puede_presentar && !enProgreso
  const agotado = bloqueado && !vencido
  const textoBoton = enProgreso
    ? 'Reanudar intento'
    : vencido
      ? 'Plazo vencido'
      : agotado
        ? 'Intentos agotados'
        : 'Presentar simulacro'

  return (
    <article
      className={cn(
        'relative flex h-full flex-col overflow-hidden rounded-2xl border',
        paletaSaberPro.superficie,
        paletaSaberPro.borde
      )}
    >
      <div aria-hidden="true" className={cn('h-1 w-full', paletaSaberPro.franja)} />
      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-2">
          <span className={cn('flex h-10 w-10 items-center justify-center rounded-xl', paletaSaberPro.iconoChip)}>
            <ClipboardList className="h-5 w-5" />
          </span>
          <div className="flex flex-wrap justify-end gap-1.5">
            <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
              {simulacro.area.nombre}
            </Badge>
            <Badge
              variant="outline"
              className="border-[#1e3a5f]/30 text-[10px] text-[#1e3a5f] dark:border-[#E3C063]/50 dark:text-[#E3C063]"
            >
              Activo
            </Badge>
            {enProgreso && (
              <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
                En progreso
              </Badge>
            )}
            {agotado && (
              <Badge
                variant="outline"
                className="border-[#b8432a]/30 text-[10px] text-[#b8432a] dark:border-[#F29A52]/40 dark:text-[#F29A52]"
              >
                Sin intentos
              </Badge>
            )}
            {vencido && !enProgreso && (
              <Badge
                variant="outline"
                className="border-[#b8432a]/30 text-[10px] text-[#b8432a] dark:border-[#F29A52]/40 dark:text-[#F29A52]"
              >
                Plazo vencido
              </Badge>
            )}
          </div>
        </div>

        <div>
          <p className={`text-[11px] font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.apoyoTitulo}`}>
            {simulacro.curso.nombre}
          </p>
          <h3 className={`mt-1 text-base font-bold leading-snug ${paletaSaberPro.titulo}`}>
            {simulacro.titulo || 'Simulacro Saber Pro'}
          </h3>
          {simulacro.descripcion && (
            <p className={`mt-1.5 line-clamp-3 text-xs leading-relaxed ${paletaSaberPro.texto}`}>
              {simulacro.descripcion}
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Dato
            icono={<ListChecks className="h-3.5 w-3.5" />}
            etiqueta="Preguntas"
            valor={`${simulacro.total_preguntas}/${simulacro.num_preguntas}`}
          />
          <Dato
            icono={<Clock className="h-3.5 w-3.5" />}
            etiqueta="Tiempo"
            valor={`${simulacro.tiempo_limite_minutos} min`}
          />
          <Dato
            icono={<Repeat className="h-3.5 w-3.5" />}
            etiqueta="Intentos"
            valor={`${simulacro.intentos_realizados}/${simulacro.intentos_maximos}`}
          />
          <Dato
            icono={<BookOpen className="h-3.5 w-3.5" />}
            etiqueta="Cierra"
            valor={
              simulacro.fecha_limite
                ? new Date(simulacro.fecha_limite).toLocaleString('es-CO', {
                    dateStyle: 'short',
                    timeStyle: 'short',
                  })
                : 'Sin límite'
            }
          />
        </div>

        <p
          className={cn(
            'text-[11px] leading-relaxed',
            agotado || (vencido && !enProgreso)
              ? 'text-[#b8432a] dark:text-[#F29A52]'
              : paletaSaberPro.apoyo
          )}
        >
          {enProgreso
            ? 'Tienes un intento en curso: retómalo para no perder el tiempo restante.'
            : vencido
              ? 'La fecha límite de este simulacro ya pasó.'
              : agotado
                ? 'Ya utilizaste todos los intentos permitidos para este simulacro.'
                : `Te queda${simulacro.intentos_restantes === 1 ? '' : 'n'} ${simulacro.intentos_restantes} de ${simulacro.intentos_maximos} intentos.`}
        </p>

        <Button
          type="button"
          disabled={bloqueado}
          className={cn('mt-auto h-10 w-full gap-2', paletaSaberPro.botonAccion)}
          onClick={() => onIniciar(simulacro)}
        >
          <Play className="h-4 w-4" />
          {textoBoton}
        </Button>
      </div>
    </article>
  )
}

export default function PaginaSimulacrosEstudianteSaberPro() {
  const navigate = useNavigate()
  const { simulacros, cargando, error, recargar } = useSimulacrosEstudianteSaberPro()
  const [cursoFiltro, setCursoFiltro] = useState<string>('todos')

  const cursos = useMemo(() => {
    const mapa = new Map<number, SimulacroEstudianteSaberPro['curso']>()
    for (const simulacro of simulacros) mapa.set(simulacro.curso.id, simulacro.curso)
    return Array.from(mapa.values())
  }, [simulacros])

  const simulacrosFiltrados = useMemo(() => {
    if (cursoFiltro === 'todos') return simulacros
    return simulacros.filter((simulacro) => simulacro.curso.id === Number(cursoFiltro))
  }, [cursoFiltro, simulacros])

  const totalPreguntas = simulacrosFiltrados.reduce((total, simulacro) => total + simulacro.total_preguntas, 0)

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />

      <div className="relative p-6 md:p-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button
              type="button"
              onClick={() => navigate('/saber-pro')}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.accion}`}
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Volver al panel
            </button>
            <h1
              className={`mt-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight ${paletaSaberPro.fuenteHero} ${paletaSaberPro.titulo}`}
            >
              Tus simulacros <span className="text-[#e8740e] dark:text-[#F29A52]">disponibles</span>
            </h1>
            <p className={`mt-2 max-w-2xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Estas evaluaciones fueron publicadas por tus docentes en los cursos a los que te uniste.
              Revisa las condiciones antes de presentar.
            </p>
          </div>
          <span className={`hidden h-16 w-16 items-center justify-center rounded-2xl sm:flex ${paletaSaberPro.chipAccion}`}>
            <GraduationCap className="h-8 w-8" />
          </span>
        </header>

        <main className="mt-8">
          {cargando && <SkeletonSimulacros />}

          {!cargando && error && <ErrorEstado mensaje={error} reintentar={() => void recargar()} />}

          {!cargando && !error && simulacros.length === 0 && (
            <section
              className={`flex flex-col items-center rounded-3xl border border-dashed p-12 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
            >
              <span className={`flex h-16 w-16 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                <ClipboardList className="h-8 w-8" />
              </span>
              <h2 className={`mt-4 text-lg font-bold ${paletaSaberPro.titulo}`}>Aun no hay simulacros para ti</h2>
              <p className={`mt-2 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>
                Cuando un docente publique un simulacro en uno de tus cursos Saber Pro, aparecera aqui
                automaticamente.
              </p>
              <Button
                type="button"
                className={`mt-5 ${paletaSaberPro.botonNeutro}`}
                onClick={() => navigate('/saber-pro')}
              >
                Volver al panel
              </Button>
            </section>
          )}

          {!cargando && !error && simulacros.length > 0 && (
            <>
              <section
                className={`rounded-2xl border p-4 md:p-5 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div className="w-full max-w-md space-y-1.5">
                    <label htmlFor="filtro-curso-simulacros" className={`text-xs font-semibold ${paletaSaberPro.titulo}`}>
                      Filtrar por curso
                    </label>
                    <Select
                      items={[
                        { value: 'todos', label: 'Todos mis cursos Saber Pro' },
                        ...cursos.map((curso) => ({ value: String(curso.id), label: curso.nombre })),
                      ]}
                      value={cursoFiltro}
                      onValueChange={(valor) => setCursoFiltro(valor ?? 'todos')}
                    >
                      <SelectTrigger id="filtro-curso-simulacros" className={selectTriggerAncho}>
                        <SelectValue placeholder="Filtrar por curso" />
                      </SelectTrigger>
                      <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                        <SelectItem value="todos" className={selectItemLargo}>
                          Todos mis cursos Saber Pro
                        </SelectItem>
                        {cursos.map((curso) => (
                          <SelectItem key={curso.id} value={String(curso.id)} className={selectItemLargo}>
                            {curso.nombre} - {curso.area.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                      {simulacrosFiltrados.length} simulacros
                    </Badge>
                    <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                      {totalPreguntas} preguntas
                    </Badge>
                  </div>
                </div>
              </section>

              <section aria-labelledby="lista-simulacros-estudiante" className="mt-6">
                <div className="flex items-center gap-3">
                  <span className={`h-6 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
                  <div>
                    <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}>
                      Evaluaciones publicadas
                    </p>
                    <h2
                      id="lista-simulacros-estudiante"
                      className={`mt-0.5 text-[22px] font-bold tracking-tight ${paletaSaberPro.titulo}`}
                    >
                      Elige tu siguiente practica
                    </h2>
                  </div>
                </div>

                {simulacrosFiltrados.length === 0 ? (
                  <div
                    className={`mt-5 flex flex-col items-center rounded-2xl border border-dashed p-10 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
                  >
                    <p className={`text-sm font-medium ${paletaSaberPro.titulo}`}>
                      Este curso no tiene simulacros publicados.
                    </p>
                  </div>
                ) : (
                  <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {simulacrosFiltrados.map((simulacro) => (
                      <TarjetaSimulacroEstudiante
                        key={simulacro.id}
                        simulacro={simulacro}
                        onIniciar={(seleccionado) => {
                          solicitarPantallaCompleta()
                          navigate(`/saber-pro/simulacros/${seleccionado.id}/presentar`)
                        }}
                      />
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
