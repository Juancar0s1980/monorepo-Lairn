// Página de analítica de resultados de un curso Saber Pro para el docente
// (HU-24.1/24.2).
//
// Ruta /saber-pro/analitica. El docente propietario elige un curso y consulta:
//   - resultados individuales de sus estudiantes (nombres visibles solo aquí),
//   - indicadores generales y distribución de calificaciones,
//   - desempeño por área, competencia y afirmación,
//   - focos de refuerzo (criterios con menor porcentaje de acierto).
// Puede filtrar por simulacro y periodo académico (AAAA-1/AAAA-2). Los filtros
// de competencia/afirmación refinan únicamente los desgloses, no el resumen ni
// los resultados individuales. En Inglés, que no usa competencias, el filtro es
// por parte del examen (1 a 7), limitado a las partes del simulacro elegido.

import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  AlertCircle,
  ArrowLeft,
  BarChart3,
  CalendarDays,
  ClipboardList,
  FileSpreadsheet,
  GraduationCap,
  Loader2,
  Target,
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
import { useAnaliticaCursoSaberPro } from '@/hooks/use-analitica-curso-saber-pro'
import { useCriteriosAreaSaberPro } from '@/hooks/use-criterios-area-saber-pro'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { useSimulacrosSaberPro } from '@/hooks/use-simulacros-saber-pro'
import type { ResultadoIndividualAnaliticaSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { mensajeError } from '@/pages/academico/academico-utils'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'
import {
  paletaSaberPro,
  selectContenidoAncho,
  selectItemLargo,
  selectTriggerAncho,
} from './utilidades'
import {
  DistribucionCalificaciones,
  EncabezadoSeccion,
  ErrorEstadoAnalitica,
  ListaFocosBajos,
  ResumenMetricas,
  TablaDesglose,
  type FilaDesgloseAnalitica,
} from './componentes/analitica-saber-pro'
import { CampanaDesbloqueosSaberPro } from './componentes/campana-desbloqueos-saber-pro'

function TarjetaFiltro({ etiqueta, htmlFor, children }: { etiqueta: string; htmlFor: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
        {etiqueta}
      </label>
      {children}
    </div>
  )
}

// Etiqueta uniforme para las partes, vengan del catálogo del área o del
// simulacro concreto (ambos usan numeración 1 a 7).
function etiquetaParte(parte: { numero: number; nombre: string }) {
  return parte.nombre.startsWith('Parte ')
    ? parte.nombre
    : `Parte ${parte.numero} · ${parte.nombre}`
}

// El naranja institucional marca las condiciones que requieren atención
// (anulada/reprobado); el dorado, la aprobación.
function EstadoIndividual({ resultado }: { resultado: ResultadoIndividualAnaliticaSaberPro }) {
  if (resultado.anulada) {
    return (
      <Badge variant="outline" className={cn('border-[#e8740e]/40', paletaSaberPro.accion)}>
        Anulada
      </Badge>
    )
  }
  return resultado.aprobado ? (
    <Badge variant="outline" className={paletaSaberPro.badge}>
      Aprobado
    </Badge>
  ) : (
    <Badge variant="outline" className={cn('border-[#e8740e]/40', paletaSaberPro.accion)}>
      Reprobado
    </Badge>
  )
}

function TablaResultadosIndividuales({ resultados }: { resultados: ResultadoIndividualAnaliticaSaberPro[] }) {
  if (resultados.length === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center rounded-2xl border border-dashed p-10 text-center',
          paletaSaberPro.bandaAlterna,
          paletaSaberPro.borde
        )}
      >
        <span className={cn('flex h-14 w-14 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
          <ClipboardList className="h-7 w-7" />
        </span>
        <p className={cn('mt-3 text-base font-bold', paletaSaberPro.titulo)}>
          Aún no hay intentos elegibles
        </p>
        <p className={cn('mt-1 max-w-md text-sm', paletaSaberPro.texto)}>
          Los resultados aparecerán cuando tus estudiantes finalicen simulacros y, si aplica,
          el docente califique las consignas abiertas.
        </p>
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto rounded-2xl border', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <Table className="bg-transparent [&_td]:text-[#2c3e50] dark:[&_td]:text-[#CFC9BA]">
        <TableHeader>
          <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
            <TableHead className={paletaSaberPro.apoyoTitulo}>Estudiante</TableHead>
            <TableHead className={paletaSaberPro.apoyoTitulo}>Simulacro</TableHead>
            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Intento</TableHead>
            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Puntaje</TableHead>
            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Calificación</TableHead>
            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Aciertos</TableHead>
            <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Estado</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {resultados.map((resultado) => (
            <TableRow
              key={`${resultado.estudiante.id}-${resultado.simulacro?.id ?? 'x'}-${resultado.intento}`}
              className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]"
            >
              <TableCell className="min-w-48 py-3">
                <p className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
                  {resultado.estudiante.nombre_completo || 'Estudiante sin nombre'}
                </p>
                <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>{resultado.estudiante.email}</p>
              </TableCell>
              <TableCell className={cn('min-w-36 py-3 text-xs', paletaSaberPro.texto)}>
                {resultado.simulacro?.titulo ?? '—'}
              </TableCell>
              <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                {resultado.intento}
              </TableCell>
              <TableCell className={cn('py-3 text-center text-xs font-semibold', paletaSaberPro.texto)}>
                {resultado.puntaje.toFixed(1)}%
              </TableCell>
              <TableCell className="py-3 text-center">
                <p
                  className={cn(
                    'text-sm font-black',
                    resultado.calificacion >= 3
                      ? paletaSaberPro.titulo
                      : paletaSaberPro.accion
                  )}
                >
                  {resultado.calificacion.toFixed(2)}
                </p>
                <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>/ 5.00</p>
              </TableCell>
              <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                {resultado.aciertos} / {resultado.total_evaluables}
              </TableCell>
              <TableCell className="py-3 text-center">
                <EstadoIndividual resultado={resultado} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export default function PaginaAnaliticaSaberPro() {
  const navigate = useNavigate()
  const {
    cursos,
    cargando: cargandoCursos,
    error: errorCursos,
    recargar: recargarCursos,
  } = useCursosSaberPro()

  const [cursoId, setCursoId] = useState<number | null>(null)
  const [simulacroId, setSimulacroId] = useState<number | null>(null)
  const [periodo, setPeriodo] = useState<string | null>(null)
  const [competenciaId, setCompetenciaId] = useState<number | null>(null)
  const [afirmacionId, setAfirmacionId] = useState<number | null>(null)
  const [parte, setParte] = useState<number | null>(null)
  const [exportando, setExportando] = useState(false)

  const cursoSeleccionado = cursos.find((curso) => curso.id === cursoId) ?? cursos[0] ?? null
  const { simulacros, cargando: cargandoSimulacros } = useSimulacrosSaberPro(
    cursoSeleccionado?.id ?? null
  )
  const { criterios, cargando: cargandoCriterios } = useCriteriosAreaSaberPro(
    cursoSeleccionado?.area.id ?? null
  )
  const { datos, cargando, error, recargar } = useAnaliticaCursoSaberPro(
    cursoSeleccionado?.id ?? null,
    {
      simulacro_id: simulacroId,
      periodo,
      competencia_id: competenciaId,
      afirmacion_id: afirmacionId,
      parte,
    }
  )

  // Ignora criterios de un área anterior mientras carga la del curso actual:
  // el hook conserva la respuesta previa hasta recibir la nueva.
  const criteriosDelCurso =
    criterios !== null && cursoSeleccionado !== null && criterios.area.id === cursoSeleccionado.area.id
      ? criterios
      : null
  const competencias = criteriosDelCurso?.competencias ?? []
  const competenciaSeleccionada = competencias.find((item) => item.id === competenciaId) ?? null
  const afirmaciones = competenciaSeleccionada?.afirmaciones ?? []
  const simulacroSeleccionado = simulacros.find((item) => item.id === simulacroId) ?? null
  const periodos = datos?.periodos_disponibles ?? []
  const tipoEstructura =
    criteriosDelCurso?.tipo_estructura ??
    (cursoSeleccionado?.area.nombre === 'Inglés'
      ? 'partes'
      : cursoSeleccionado?.area.nombre === 'Comunicación Escrita'
        ? 'consigna'
        : 'competencias')
  const esIngles = tipoEstructura === 'partes'
  const sinCriterios =
    criteriosDelCurso !== null && !esIngles && tipoEstructura !== 'competencias'
  const partesDisponibles = useMemo(() => {
    if (!esIngles) return []
    const base =
      criteriosDelCurso?.partes.map((item) => ({ numero: item.numero, nombre: item.nombre })) ??
      datos?.partes_disponibles ??
      []
    const configuradas = new Set(
      (simulacroSeleccionado?.distribuciones ?? [])
        .map((distribucion) => distribucion.parte)
        .filter((numero): numero is number => numero !== null)
    )
    return base.filter(
      (item) => configuradas.size === 0 || configuradas.has(item.numero)
    )
  }, [criteriosDelCurso, datos, esIngles, simulacroSeleccionado])

  const filasArea = useMemo<FilaDesgloseAnalitica[]>(
    () =>
      (datos?.por_area ?? []).map((item) => ({
        clave: `area-${item.area.id}`,
        nombre: item.area.nombre,
        aciertos: item.aciertos,
        total_preguntas: item.total_preguntas,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const filasCompetencia = useMemo<FilaDesgloseAnalitica[]>(
    () =>
      (datos?.por_competencia ?? []).map((item) => ({
        clave: `competencia-${item.competencia.id}`,
        nombre: item.competencia.nombre,
        detalle: item.area.nombre,
        aciertos: item.aciertos,
        total_preguntas: item.total_preguntas,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const filasAfirmacion = useMemo<FilaDesgloseAnalitica[]>(
    () =>
      (datos?.por_afirmacion ?? []).map((item) => ({
        clave: `afirmacion-${item.afirmacion.id}`,
        nombre: item.afirmacion.nombre,
        detalle: `${item.area.nombre} · ${item.competencia.nombre}`,
        aciertos: item.aciertos,
        total_preguntas: item.total_preguntas,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const filasParte = useMemo<FilaDesgloseAnalitica[]>(
    () =>
      (datos?.por_parte ?? []).map((item) => ({
        clave: `parte-${item.parte.numero}`,
        nombre: etiquetaParte(item.parte),
        aciertos: item.aciertos,
        total_preguntas: item.total_preguntas,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const cambiarCurso = (valor: string | null) => {
    if (!valor) return
    setCursoId(Number(valor))
    setSimulacroId(null)
    setPeriodo(null)
    setCompetenciaId(null)
    setAfirmacionId(null)
    setParte(null)
  }

  const exportar = async () => {
    if (!cursoSeleccionado) return
    setExportando(true)
    try {
      const consulta = new URLSearchParams()
      if (simulacroId !== null) consulta.set('simulacro_id', String(simulacroId))
      if (periodo) consulta.set('periodo', periodo)
      if (competenciaId !== null) consulta.set('competencia_id', String(competenciaId))
      if (afirmacionId !== null) consulta.set('afirmacion_id', String(afirmacionId))
      if (parte !== null) consulta.set('parte', String(parte))
      const sufijo = consulta.toString() ? `?${consulta.toString()}` : ''
      await descargarArchivo(
        `/saber-pro/docente/cursos/${cursoSeleccionado.id}/analitica/exportar/${sufijo}`,
        `analitica_curso_${cursoSeleccionado.id}.xlsx`
      )
    } catch (err) {
      toast.error(mensajeError(err, 'No se pudo exportar la analítica del curso'))
    } finally {
      setExportando(false)
    }
  }

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
              Analítica <span className={paletaSaberPro.accion}>Saber Pro</span>
            </h1>
            <p className={cn('mt-2 max-w-2xl text-sm leading-relaxed', paletaSaberPro.texto)}>
              Consulta los resultados individuales y agregados de tu curso, filtra por simulacro o
              periodo y detecta las áreas, competencias, afirmaciones o partes de Inglés que
              necesitan refuerzo.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              className={cn('gap-2', paletaSaberPro.botonNeutro)}
              onClick={() => void exportar()}
              disabled={!datos || cargando || exportando}
            >
              {exportando ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <FileSpreadsheet className="h-4 w-4" aria-hidden />
              )}
              {exportando ? 'Generando Excel...' : 'Exportar Excel'}
            </Button>
            <CampanaDesbloqueosSaberPro />
            <span
              className={cn(
                'hidden h-16 w-16 items-center justify-center rounded-2xl sm:flex',
                paletaSaberPro.chipGold
              )}
            >
              <BarChart3 className="h-8 w-8" />
            </span>
          </div>
        </header>

        {cargandoCursos && (
          <div className={cn('mt-8 flex items-center gap-2 text-sm', paletaSaberPro.apoyo)}>
            <Loader2 className="h-4 w-4 animate-spin" /> Cargando tus cursos...
          </div>
        )}

        {!cargandoCursos && errorCursos && (
          <div className="mt-8">
            <ErrorEstadoAnalitica mensaje={errorCursos} reintentar={() => void recargarCursos()} />
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
              La analítica se calcula con los resultados de los simulacros de cada curso Saber Pro.
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
              aria-label="Filtros de la analítica"
              className={cn('rounded-2xl border p-4 md:p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}
            >
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <TarjetaFiltro etiqueta="Curso Saber Pro" htmlFor="analitica-curso">
                  <Select
                    items={cursos.map((curso) => ({
                      value: String(curso.id),
                      label: `${curso.nombre} - ${curso.area.nombre}`,
                    }))}
                    value={String(cursoSeleccionado.id)}
                    onValueChange={cambiarCurso}
                  >
                    <SelectTrigger id="analitica-curso" className={selectTriggerAncho}>
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
                </TarjetaFiltro>

                <TarjetaFiltro etiqueta="Simulacro" htmlFor="analitica-simulacro">
                  <Select
                    items={[
                      { value: 'todos', label: 'Todos los simulacros' },
                      ...simulacros.map((simulacro) => ({
                        value: String(simulacro.id),
                        label: simulacro.titulo || `Simulacro #${simulacro.id}`,
                      })),
                    ]}
                    value={simulacroId === null ? 'todos' : String(simulacroId)}
                    onValueChange={(valor) => {
                      setSimulacroId(valor === 'todos' ? null : Number(valor))
                      setPeriodo(null)
                      setParte(null)
                    }}
                  >
                    <SelectTrigger id="analitica-simulacro" className={selectTriggerAncho}>
                      <SelectValue placeholder="Todos los simulacros" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todos" className={selectItemLargo}>
                        Todos los simulacros
                      </SelectItem>
                      {simulacros.map((simulacro) => (
                        <SelectItem key={simulacro.id} value={String(simulacro.id)} className={selectItemLargo}>
                          {simulacro.titulo || `Simulacro #${simulacro.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {cargandoSimulacros && (
                    <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>Cargando simulacros...</p>
                  )}
                </TarjetaFiltro>

                <TarjetaFiltro etiqueta="Periodo académico" htmlFor="analitica-periodo">
                  <Select
                    items={[
                      { value: 'todos', label: 'Todos los periodos' },
                      ...periodos.map((item) => ({ value: item, label: item })),
                    ]}
                    value={periodo ?? 'todos'}
                    onValueChange={(valor) => setPeriodo(valor === 'todos' ? null : valor)}
                  >
                    <SelectTrigger id="analitica-periodo" className={selectTriggerAncho}>
                      <SelectValue placeholder="Todos los periodos" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todos" className={selectItemLargo}>
                        Todos los periodos
                      </SelectItem>
                      {periodos.map((item) => (
                        <SelectItem key={item} value={item} className={selectItemLargo}>
                          {item}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TarjetaFiltro>

                {esIngles ? (
                  <TarjetaFiltro etiqueta="Parte del examen" htmlFor="analitica-parte">
                    <Select
                      items={[
                        { value: 'todas', label: 'Todas las partes' },
                        ...partesDisponibles.map((item) => ({
                          value: String(item.numero),
                          label: etiquetaParte(item),
                        })),
                      ]}
                      value={parte === null ? 'todas' : String(parte)}
                      onValueChange={(valor) =>
                        setParte(valor === 'todas' ? null : Number(valor))
                      }
                      disabled={partesDisponibles.length === 0}
                    >
                      <SelectTrigger id="analitica-parte" className={selectTriggerAncho}>
                        <SelectValue placeholder="Todas las partes" />
                      </SelectTrigger>
                      <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                        <SelectItem value="todas" className={selectItemLargo}>
                          Todas las partes
                        </SelectItem>
                        {partesDisponibles.map((item) => (
                          <SelectItem
                            key={item.numero}
                            value={String(item.numero)}
                            className={selectItemLargo}
                          >
                            {etiquetaParte(item)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TarjetaFiltro>
                ) : (
                  <>
                    <TarjetaFiltro etiqueta="Competencia" htmlFor="analitica-competencia">
                      <Select
                        items={[
                          { value: 'todas', label: 'Todas las competencias' },
                          ...competencias.map((item) => ({ value: String(item.id), label: item.nombre })),
                        ]}
                        value={competenciaId === null ? 'todas' : String(competenciaId)}
                        onValueChange={(valor) => {
                          setCompetenciaId(valor === 'todas' ? null : Number(valor))
                          setAfirmacionId(null)
                        }}
                        disabled={sinCriterios || competencias.length === 0}
                      >
                        <SelectTrigger id="analitica-competencia" className={selectTriggerAncho}>
                          <SelectValue placeholder="Todas las competencias" />
                        </SelectTrigger>
                        <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                          <SelectItem value="todas" className={selectItemLargo}>
                            Todas las competencias
                          </SelectItem>
                          {competencias.map((item) => (
                            <SelectItem key={item.id} value={String(item.id)} className={selectItemLargo}>
                              {item.nombre}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {cargandoCriterios && (
                        <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>Cargando criterios...</p>
                      )}
                    </TarjetaFiltro>

                    <TarjetaFiltro etiqueta="Afirmación" htmlFor="analitica-afirmacion">
                      <Select
                        items={[
                          { value: 'todas', label: 'Todas las afirmaciones' },
                          ...afirmaciones.map((item) => ({ value: String(item.id), label: item.nombre })),
                        ]}
                        value={afirmacionId === null ? 'todas' : String(afirmacionId)}
                        onValueChange={(valor) => setAfirmacionId(valor === 'todas' ? null : Number(valor))}
                        disabled={afirmaciones.length === 0}
                      >
                        <SelectTrigger id="analitica-afirmacion" className={selectTriggerAncho}>
                          <SelectValue placeholder="Todas las afirmaciones" />
                        </SelectTrigger>
                        <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                          <SelectItem value="todas" className={selectItemLargo}>
                            Todas las afirmaciones
                          </SelectItem>
                          {afirmaciones.map((item) => (
                            <SelectItem key={item.id} value={String(item.id)} className={selectItemLargo}>
                              {item.nombre}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TarjetaFiltro>
                  </>
                )}
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {cursoSeleccionado.area.nombre}
                </Badge>
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {simulacroSeleccionado ? 'Simulacro específico' : 'Todos los simulacros'}
                </Badge>
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  <CalendarDays className="mr-1 h-3 w-3" /> {periodo ?? 'Todos los periodos'}
                </Badge>
                {esIngles && parte !== null && (
                  <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                    {etiquetaParte(
                      partesDisponibles.find((item) => item.numero === parte) ?? {
                        numero: parte,
                        nombre: `Parte ${parte}`,
                      }
                    )}
                  </Badge>
                )}
                {sinCriterios && (
                  <span className={cn('text-[11px]', paletaSaberPro.apoyo)}>
                    Esta área no usa competencias/afirmaciones; se evalúa por sus propios criterios.
                  </span>
                )}
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
                <p className={cn('text-sm', paletaSaberPro.texto)}>Calculando analítica del curso...</p>
              </div>
            )}

            {!cargando && error && (
              <div className="mt-6">
                <ErrorEstadoAnalitica mensaje={error} reintentar={() => void recargar()} />
              </div>
            )}

            {!cargando && !error && datos && (
              <>
                <section aria-labelledby="resumen-analitica" className="mt-8">
                  <EncabezadoSeccion
                    id="resumen-analitica"
                    eyebrow="Panorama del grupo"
                    titulo="Indicadores generales"
                  />
                  <div className="mt-5">
                    <ResumenMetricas resumen={datos.resumen} />
                  </div>
                  <p className={cn('mt-2 text-[11px]', paletaSaberPro.apoyo)}>
                    {datos.resumen.total_estudiantes} estudiantes · {datos.resumen.total_intentos}{' '}
                    intentos elegibles · promedio de puntaje {datos.resumen.promedio_puntaje.toFixed(1)}%
                  </p>
                </section>

                <section className="mt-8 grid gap-4 lg:grid-cols-2">
                  <DistribucionCalificaciones datos={datos.distribucion_calificaciones} />
                  <ListaFocosBajos focos={datos.focos_bajos} />
                </section>

                <section aria-labelledby="desglose-analitica" className="mt-8 space-y-4">
                  <EncabezadoSeccion
                    id="desglose-analitica"
                    eyebrow="Dónde reforzar"
                    titulo="Desempeño por criterio"
                  />
                  <TablaDesglose
                    titulo="Por área"
                    filas={filasArea}
                    vacio="No hay ítems evaluados para las áreas del curso."
                  />
                  {esIngles ? (
                    <TablaDesglose
                      titulo="Por parte del examen"
                      descripcion={
                        parte === null
                          ? 'Partes 1 a 7, de menor a mayor acierto'
                          : 'Parte seleccionada'
                      }
                      filas={filasParte}
                      vacio="El curso no tiene ítems evaluados de Inglés con los filtros aplicados."
                    />
                  ) : (
                    <>
                      <TablaDesglose
                        titulo="Por competencia"
                        descripcion="Ordenadas de menor a mayor acierto"
                        filas={filasCompetencia}
                        vacio="El área del curso no tiene competencias evaluadas."
                      />
                      <TablaDesglose
                        titulo="Por afirmación"
                        descripcion="Ordenadas de menor a mayor acierto"
                        filas={filasAfirmacion}
                        vacio="El área del curso no tiene afirmaciones evaluadas."
                      />
                    </>
                  )}
                </section>

                <section aria-labelledby="resultados-individuales" className="mt-8">
                  <EncabezadoSeccion
                    id="resultados-individuales"
                    eyebrow="Trazabilidad"
                    titulo="Resultados individuales"
                  />
                  <div className="mt-5">
                    <TablaResultadosIndividuales resultados={datos.resultados_individuales} />
                  </div>
                  <p className={cn('mt-3 flex items-center gap-1.5 text-[11px]', paletaSaberPro.apoyo)}>
                    <Users className="h-3 w-3" /> Los nombres solo están visibles para ti como docente
                    del curso. Los intentos anulados conservan sus ítems en el denominador.
                  </p>
                </section>

                <section className={cn('mt-8 flex items-start gap-3 rounded-2xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
                  <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-xl', paletaSaberPro.chipAccion)}>
                    <Target className="h-4 w-4" />
                  </span>
                  <p className={cn('text-xs leading-relaxed', paletaSaberPro.apoyo)}>
                    Solo se consideran intentos finalizados y calificados. El periodo se deriva de la
                    fecha de finalización (enero-junio = AAAA-1; julio-diciembre = AAAA-2). Los filtros
                    de competencia, afirmación o parte refinan los desgloses, no el resumen ni los
                    resultados individuales.
                  </p>
                </section>

                {datos.resultados_individuales.length === 0 && (
                  <div className={cn('mt-4 flex items-center gap-2 text-xs', paletaSaberPro.apoyo)}>
                    <AlertCircle className="h-3.5 w-3.5" /> Ajusta los filtros o espera a que se
                    registren intentos elegibles.
                  </div>
                )}
              </>
            )}
          </main>
        )}
      </div>
    </div>
  )
}
