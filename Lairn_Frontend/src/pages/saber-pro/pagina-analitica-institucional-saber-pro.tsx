// Página de analítica académica institucional de Saber Pro (HU-24.3/24.4).
//
// Ruta /saber-pro/institucional/analitica. Dirigida a Coordinación y
// Vicerrectoría (el permiso `EsLectorAnalitica` también cubre al Administrador
// en lectura). Consulta todos los cursos Saber Pro de la institución y muestra:
//   - indicadores consolidados y distribución de calificaciones,
//   - desempeño por área, competencia y afirmación,
//   - comparativas entre cursos, carreras y periodos académicos,
//   - focos de refuerzo institucionales.
// Por privacidad NO expone resultados individuales (HU-24.4.6). Los filtros
// permiten acotar por carrera, curso, área y periodo (AAAA-1/AAAA-2). Cuando el
// área es Inglés se habilita además el filtro por parte del examen (1 a 7).

import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ArrowLeft,
  BarChart3,
  CalendarDays,
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
import { useAnaliticaInstitucionalSaberPro } from '@/hooks/use-analitica-institucional-saber-pro'
import { useCatalogoInstitucionalSaberPro } from '@/hooks/use-catalogo-institucional-saber-pro'
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
  TablaComparativa,
  TablaDesglose,
  type FilaComparativaAnalitica,
  type FilaDesgloseAnalitica,
} from './componentes/analitica-saber-pro'

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

function etiquetaParte(parte: { numero: number; nombre: string }) {
  return parte.nombre.startsWith('Parte ')
    ? parte.nombre
    : `Parte ${parte.numero} · ${parte.nombre}`
}

export default function PaginaAnaliticaInstitucionalSaberPro() {
  const navigate = useNavigate()
  const {
    catalogo,
    cargando: cargandoCatalogo,
    error: errorCatalogo,
    recargar: recargarCatalogo,
  } = useCatalogoInstitucionalSaberPro()

  const [programaId, setProgramaId] = useState<number | null>(null)
  const [cursoId, setCursoId] = useState<number | null>(null)
  const [areaId, setAreaId] = useState<number | null>(null)
  const [periodo, setPeriodo] = useState<string | null>(null)
  const [parte, setParte] = useState<number | null>(null)
  const [exportando, setExportando] = useState(false)

  const { datos, cargando, error, recargar } = useAnaliticaInstitucionalSaberPro({
    curso_id: cursoId,
    programa_id: programaId,
    area_id: areaId,
    competencia_id: null,
    afirmacion_id: null,
    parte,
    periodo,
  })

  const cursoSeleccionado = catalogo?.cursos.find((curso) => curso.id === cursoId) ?? null
  const areaSeleccionada = catalogo?.areas.find((area) => area.id === areaId) ?? null
  const programaSeleccionado =
    catalogo?.programas.find((programa) => programa.id === programaId) ?? null
  const periodos = datos?.periodos_disponibles ?? []
  const esIngles = areaSeleccionada?.nombre === 'Inglés'
  const partesDisponibles = esIngles ? datos?.partes_disponibles ?? [] : []

  const cursosDisponibles = useMemo(() => {
    if (!catalogo) return []
    if (areaId === null) return catalogo.cursos
    return catalogo.cursos.filter((curso) => curso.area.id === areaId)
  }, [catalogo, areaId])

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

  const filasCurso = useMemo<FilaComparativaAnalitica[]>(
    () =>
      (datos?.por_curso ?? []).map((item) => ({
        clave: `curso-${item.curso.id}`,
        nombre: item.curso.nombre,
        detalle: item.curso.area.nombre,
        total_estudiantes: item.total_estudiantes,
        total_intentos: item.total_intentos,
        promedio_calificacion: item.promedio_calificacion,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const filasPrograma = useMemo<FilaComparativaAnalitica[]>(
    () =>
      (datos?.por_programa ?? []).map((item) => ({
        clave: `programa-${item.programa.id}`,
        nombre: item.programa.nombre,
        total_estudiantes: item.total_estudiantes,
        total_intentos: item.total_intentos,
        promedio_calificacion: item.promedio_calificacion,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const filasPeriodo = useMemo<FilaComparativaAnalitica[]>(
    () =>
      (datos?.por_periodo ?? []).map((item) => ({
        clave: `periodo-${item.periodo}`,
        nombre: item.periodo,
        total_estudiantes: item.total_estudiantes,
        total_intentos: item.total_intentos,
        promedio_calificacion: item.promedio_calificacion,
        porcentaje_acierto: item.porcentaje_acierto,
      })),
    [datos]
  )

  const cambiarCurso = (valor: string | null) => {
    if (!valor) return
    setPeriodo(null)
    setParte(null)
    if (valor === 'todos') {
      setCursoId(null)
      return
    }
    const nuevoId = Number(valor)
    setCursoId(nuevoId)
    const curso = catalogo?.cursos.find((item) => item.id === nuevoId)
    if (curso) setAreaId(curso.area.id)
  }

  const cambiarArea = (valor: string | null) => {
    if (!valor) return
    setPeriodo(null)
    setParte(null)
    if (valor === 'todas') {
      setAreaId(null)
      return
    }
    const nuevoId = Number(valor)
    setAreaId(nuevoId)
    if (cursoSeleccionado && cursoSeleccionado.area.id !== nuevoId) {
      setCursoId(null)
    }
  }

  const exportar = async () => {
    setExportando(true)
    try {
      const consulta = new URLSearchParams()
      if (cursoId !== null) consulta.set('curso_id', String(cursoId))
      if (programaId !== null) consulta.set('programa_id', String(programaId))
      if (areaId !== null) consulta.set('area_id', String(areaId))
      if (parte !== null) consulta.set('parte', String(parte))
      if (periodo) consulta.set('periodo', periodo)
      const sufijo = consulta.toString() ? `?${consulta.toString()}` : ''
      await descargarArchivo(
        `/saber-pro/institucional/analitica/exportar/${sufijo}`,
        'analitica_institucional.xlsx'
      )
    } catch (err) {
      toast.error(mensajeError(err, 'No se pudo exportar la analítica institucional'))
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
              onClick={() => navigate('/')}
              className={cn(
                'inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em]',
                paletaSaberPro.accion
              )}
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Volver al inicio
            </button>
            <h1
              className={cn(
                'mt-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight',
                paletaSaberPro.fuenteHero,
                paletaSaberPro.titulo
              )}
            >
              Analítica institucional{' '}
              <span className={paletaSaberPro.accion}>Saber Pro</span>
            </h1>
            <p className={cn('mt-2 max-w-2xl text-sm leading-relaxed', paletaSaberPro.texto)}>
              Consulta el desempeño consolidado de todos los cursos Saber Pro y compara por curso,
              carrera y periodo académico. En Inglés puedes filtrar por parte del examen. Vista
              agregada: no expone resultados individuales.
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
            <span
              className={cn(
                'hidden h-16 w-16 items-center justify-center rounded-2xl sm:flex',
                paletaSaberPro.chipGold
              )}
            >
              <GraduationCap className="h-8 w-8" />
            </span>
          </div>
        </header>

        {cargandoCatalogo && (
          <div className={cn('mt-8 flex items-center gap-2 text-sm', paletaSaberPro.apoyo)}>
            <Loader2 className="h-4 w-4 animate-spin" /> Cargando catálogo institucional...
          </div>
        )}

        {!cargandoCatalogo && errorCatalogo && (
          <div className="mt-8">
            <ErrorEstadoAnalitica mensaje={errorCatalogo} reintentar={() => void recargarCatalogo()} />
          </div>
        )}

        {!cargandoCatalogo && !errorCatalogo && catalogo && (
          <main className="mt-8">
            <section
              aria-label="Filtros de la analítica institucional"
              className={cn('rounded-2xl border p-4 md:p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}
            >
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <TarjetaFiltro etiqueta="Carrera" htmlFor="institucional-programa">
                  <Select
                    items={[
                      { value: 'todas', label: 'Todas las carreras' },
                      ...catalogo.programas.map((programa) => ({
                        value: String(programa.id),
                        label: programa.nombre,
                      })),
                    ]}
                    value={programaId === null ? 'todas' : String(programaId)}
                    onValueChange={(valor) => {
                      setProgramaId(valor === 'todas' ? null : Number(valor))
                      setPeriodo(null)
                    }}
                  >
                    <SelectTrigger id="institucional-programa" className={selectTriggerAncho}>
                      <SelectValue placeholder="Todas las carreras" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todas" className={selectItemLargo}>
                        Todas las carreras
                      </SelectItem>
                      {catalogo.programas.map((programa) => (
                        <SelectItem
                          key={programa.id}
                          value={String(programa.id)}
                          className={selectItemLargo}
                        >
                          {programa.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TarjetaFiltro>

                <TarjetaFiltro etiqueta="Curso Saber Pro" htmlFor="institucional-curso">
                  <Select
                    items={[
                      { value: 'todos', label: 'Todos los cursos' },
                      ...cursosDisponibles.map((curso) => ({
                        value: String(curso.id),
                        label: `${curso.nombre} - ${curso.area.nombre}`,
                      })),
                    ]}
                    value={cursoId === null ? 'todos' : String(cursoId)}
                    onValueChange={cambiarCurso}
                  >
                    <SelectTrigger id="institucional-curso" className={selectTriggerAncho}>
                      <SelectValue placeholder="Todos los cursos" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todos" className={selectItemLargo}>
                        Todos los cursos
                      </SelectItem>
                      {cursosDisponibles.map((curso) => (
                        <SelectItem key={curso.id} value={String(curso.id)} className={selectItemLargo}>
                          {curso.nombre} - {curso.area.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TarjetaFiltro>

                <TarjetaFiltro etiqueta="Área" htmlFor="institucional-area">
                  <Select
                    items={[
                      { value: 'todas', label: 'Todas las áreas' },
                      ...catalogo.areas.map((area) => ({
                        value: String(area.id),
                        label: area.nombre,
                      })),
                    ]}
                    value={areaId === null ? 'todas' : String(areaId)}
                    onValueChange={cambiarArea}
                  >
                    <SelectTrigger id="institucional-area" className={selectTriggerAncho}>
                      <SelectValue placeholder="Todas las áreas" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      <SelectItem value="todas" className={selectItemLargo}>
                        Todas las áreas
                      </SelectItem>
                      {catalogo.areas.map((area) => (
                        <SelectItem key={area.id} value={String(area.id)} className={selectItemLargo}>
                          {area.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TarjetaFiltro>

                {esIngles && (
                  <TarjetaFiltro etiqueta="Parte del examen" htmlFor="institucional-parte">
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
                      <SelectTrigger id="institucional-parte" className={selectTriggerAncho}>
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
                )}

                <TarjetaFiltro etiqueta="Periodo académico" htmlFor="institucional-periodo">
                  <Select
                    items={[
                      { value: 'todos', label: 'Todos los periodos' },
                      ...periodos.map((item) => ({ value: item, label: item })),
                    ]}
                    value={periodo ?? 'todos'}
                    onValueChange={(valor) => setPeriodo(valor === 'todos' ? null : valor)}
                  >
                    <SelectTrigger id="institucional-periodo" className={selectTriggerAncho}>
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
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {programaSeleccionado?.nombre ?? 'Todas las carreras'}
                </Badge>
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {cursoSeleccionado?.nombre ?? 'Todos los cursos'}
                </Badge>
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  {areaSeleccionada?.nombre ?? 'Todas las áreas'}
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
                <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                  <CalendarDays className="mr-1 h-3 w-3" /> {periodo ?? 'Todos los periodos'}
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
                <p className={cn('text-sm', paletaSaberPro.texto)}>Consolidando la analítica...</p>
              </div>
            )}

            {!cargando && error && (
              <div className="mt-6">
                <ErrorEstadoAnalitica mensaje={error} reintentar={() => void recargar()} />
              </div>
            )}

            {!cargando && !error && datos && (
              <>
                <section aria-labelledby="resumen-institucional" className="mt-8">
                  <EncabezadoSeccion
                    id="resumen-institucional"
                    eyebrow="Panorama institucional"
                    titulo="Indicadores consolidados"
                  />
                  <div className="mt-5">
                    <ResumenMetricas resumen={datos.resumen} institucional />
                  </div>
                  <p className={cn('mt-2 text-[11px]', paletaSaberPro.apoyo)}>
                    {datos.resumen.total_intentos} intentos elegibles · promedio de puntaje{' '}
                    {datos.resumen.promedio_puntaje.toFixed(1)}%
                  </p>
                </section>

                <section className="mt-8 grid gap-4 lg:grid-cols-2">
                  <DistribucionCalificaciones datos={datos.distribucion_calificaciones} />
                  <ListaFocosBajos focos={datos.focos_bajos} />
                </section>

                <section aria-labelledby="desglose-institucional" className="mt-8 space-y-4">
                  <EncabezadoSeccion
                    id="desglose-institucional"
                    eyebrow="Dónde reforzar"
                    titulo="Desempeño por criterio"
                  />
                  <TablaDesglose
                    titulo="Por área"
                    filas={filasArea}
                    vacio="No hay ítems evaluados en el conjunto consultado."
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
                      vacio="El conjunto consultado no tiene ítems evaluados de Inglés con los filtros aplicados."
                    />
                  ) : (
                    <>
                      <TablaDesglose
                        titulo="Por competencia"
                        descripcion="Ordenadas de menor a mayor acierto"
                        filas={filasCompetencia}
                        vacio="Las áreas consultadas no tienen competencias evaluadas."
                      />
                      <TablaDesglose
                        titulo="Por afirmación"
                        descripcion="Ordenadas de menor a mayor acierto"
                        filas={filasAfirmacion}
                        vacio="Las áreas consultadas no tienen afirmaciones evaluadas."
                      />
                    </>
                  )}
                </section>

                <section aria-labelledby="comparativas-institucional" className="mt-8 space-y-4">
                  <EncabezadoSeccion
                    id="comparativas-institucional"
                    eyebrow="Comparación"
                    titulo="Cursos, carreras y periodos"
                  />
                  <TablaComparativa
                    titulo="Por curso"
                    filas={filasCurso}
                    vacio="No hay cursos con intentos elegibles."
                  />
                  <TablaComparativa
                    titulo="Por carrera"
                    filas={filasPrograma}
                    vacio="No hay estudiantes con carrera asociada e intentos elegibles."
                  />
                  <TablaComparativa
                    titulo="Por periodo"
                    filas={filasPeriodo}
                    vacio="No hay intentos elegibles para agrupar por periodo."
                  />
                </section>

                <section
                  className={cn(
                    'mt-8 flex items-start gap-3 rounded-2xl border p-4',
                    paletaSaberPro.superficie,
                    paletaSaberPro.borde
                  )}
                >
                  <span
                    className={cn(
                      'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
                      paletaSaberPro.chipAccion
                    )}
                  >
                    <Target className="h-4 w-4" />
                  </span>
                  <p className={cn('text-xs leading-relaxed', paletaSaberPro.apoyo)}>
                    Solo se consideran intentos finalizados y calificados de estudiantes con perfil
                    académico. El periodo se deriva de la fecha de finalización y las comparativas
                    institucionales son agregadas: no se muestran nombres ni resultados individuales.
                    En Inglés el desglose y el filtro propios son las partes del examen.
                  </p>
                </section>

                <p className={cn('mt-4 flex items-center gap-1.5 text-[11px]', paletaSaberPro.apoyo)}>
                  <Users className="h-3 w-3" /> {datos.resumen.total_estudiantes} estudiantes y{' '}
                  {datos.resumen.total_cursos} cursos en el conjunto consultado.
                </p>

                <div className="mt-6 flex flex-wrap gap-2">
                  <Button
                    type="button"
                    className={cn('gap-2', paletaSaberPro.botonNeutro)}
                    onClick={() => navigate('/reporte-institucional')}
                  >
                    <BarChart3 className="h-4 w-4" /> Ir al reporte institucional
                  </Button>
                </div>
              </>
            )}
          </main>
        )}
      </div>
    </div>
  )
}
