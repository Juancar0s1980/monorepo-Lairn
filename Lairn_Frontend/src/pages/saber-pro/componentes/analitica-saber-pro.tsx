// Componentes compartidos de las vistas de analítica Saber Pro (HU-24).
//
// Reúnen los bloques visuales que usan tanto la analítica del docente como la
// institucional: encabezados de sección, tarjetas de indicadores, distribución
// de calificaciones, focos de bajo desempeño y tablas de desglose. Se aplica la
// identidad visual institucional (beige/navy/dorado/naranja) con variantes
// oscuras simétricas definidas en `../utilidades.ts`.

import type { ReactNode } from 'react'
import { AlertCircle, BarChart3, Loader2, Sparkles, Target } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type {
  AccionAnalisisSaberPro,
  AnalisisAccionesSaberPro,
  DistribucionCalificacionAnaliticaSaberPro,
  FocoBajoAnaliticaSaberPro,
  ResumenAnaliticaSaberPro,
} from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

// Fila normalizada de una tabla de desglose (área, competencia, afirmación,
// parte de Inglés, curso, carrera o periodo). `detalle` es contexto opcional
// (p. ej. el área de una competencia o el número de intentos de un curso).
export interface FilaDesgloseAnalitica {
  clave: string
  nombre: string
  detalle?: string
  aciertos: number
  total_preguntas: number
  porcentaje_acierto: number
}

// Fila de una comparativa institucional (curso, carrera o periodo): en lugar de
// aciertos/ítems muestra estudiantes, intentos y promedio de calificación.
export interface FilaComparativaAnalitica {
  clave: string
  nombre: string
  detalle?: string
  total_estudiantes: number
  total_intentos: number
  promedio_calificacion: number
  porcentaje_acierto: number
}

// Color del badge de prioridad según la paleta institucional: naranja para
// alta (acción urgente), dorado para media y muted para baja.
export function PrioridadAccion({
  prioridad,
}: {
  prioridad: AccionAnalisisSaberPro['prioridad']
}) {
  const estilo =
    prioridad === 'alta'
      ? paletaSaberPro.accion
      : prioridad === 'media'
        ? paletaSaberPro.apoyoTitulo
        : paletaSaberPro.apoyo
  return (
    <Badge
      variant="outline"
      className={cn('text-[10px] font-bold uppercase tracking-[0.08em]', estilo)}
    >
      {prioridad}
    </Badge>
  )
}

// Sección del análisis de acciones con IA: carga, error con reintento, estado
// vacío (invita a generarlo) y plan generado (resumen + acciones). Se reutiliza
// en la analítica del curso (docente) y en la institucional (coordinación y
// vicerrectoría); `alcance` solo ajusta los textos.
export function SeccionAnalisisAcciones({
  analisis,
  cargando,
  error,
  onGenerar,
  alcance = 'curso',
}: {
  analisis: Pick<AnalisisAccionesSaberPro, 'resumen' | 'acciones'> | null
  cargando: boolean
  error: string | null
  onGenerar: () => void
  alcance?: 'curso' | 'institucional'
}) {
  const institucional = alcance === 'institucional'
  if (cargando) {
    return (
      <div
        className={cn(
          'flex min-h-40 flex-col items-center justify-center gap-3 rounded-2xl border',
          paletaSaberPro.superficie,
          paletaSaberPro.borde
        )}
      >
        <Loader2 className={cn('h-8 w-8 animate-spin', paletaSaberPro.accion)} />
        <p className={cn('text-sm', paletaSaberPro.texto)}>
          La IA está analizando la analítica {institucional ? 'institucional' : 'del curso'}...
        </p>
        <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>
          Puede tardar unos segundos. No cierres esta página.
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('rounded-2xl border p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}>
        <p className={cn('flex items-center gap-2 text-sm font-medium', paletaSaberPro.accion)}>
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden /> {error}
        </p>
        <Button
          type="button"
          className={cn('mt-4 gap-2', paletaSaberPro.botonNeutro)}
          onClick={onGenerar}
        >
          Reintentar
        </Button>
      </div>
    )
  }

  if (!analisis) {
    return (
      <div
        className={cn(
          'flex flex-col items-center rounded-2xl border border-dashed p-8 text-center',
          paletaSaberPro.bandaAlterna,
          paletaSaberPro.borde
        )}
      >
        <span className={cn('flex h-12 w-12 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
          <Sparkles className="h-6 w-6" />
        </span>
        <p className={cn('mt-3 text-sm font-bold', paletaSaberPro.titulo)}>
          ¿Qué hacer con estos resultados?
        </p>
        <p className={cn('mt-1 max-w-md text-sm leading-relaxed', paletaSaberPro.texto)}>
          Genera con IA un análisis de acciones a partir de los informes y los
          filtros actuales:{' '}
          {institucional
            ? 'prioridades de refuerzo y pasos concretos para la institución.'
            : 'prioridades de refuerzo y pasos concretos para tu curso.'}
        </p>
        <Button
          type="button"
          className={cn('mt-4 gap-2', paletaSaberPro.botonAccion)}
          onClick={onGenerar}
        >
          <Sparkles className="h-4 w-4" aria-hidden /> Generar análisis con IA
        </Button>
      </div>
    )
  }

  return (
    <div className={cn('rounded-2xl border p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <p className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>{analisis.resumen}</p>
      <ol className="mt-5 space-y-3">
        {analisis.acciones.map((accion, indice) => (
          <li key={`${indice}-${accion.titulo}`} className="flex items-start gap-3">
            <span
              className={cn(
                'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold',
                paletaSaberPro.numeracionPaso
              )}
            >
              {indice + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>{accion.titulo}</p>
                <PrioridadAccion prioridad={accion.prioridad} />
              </div>
              <p className={cn('mt-1 text-xs leading-relaxed', paletaSaberPro.apoyo)}>
                {accion.descripcion}
              </p>
            </div>
          </li>
        ))}
      </ol>
      <p className={cn('mt-4 flex items-center gap-1.5 text-[11px]', paletaSaberPro.apoyo)}>
        <Sparkles className="h-3 w-3 shrink-0" aria-hidden /> Generado con IA a partir de
        los filtros aplicados; uso orientativo, la decisión académica es tuya.
      </p>
    </div>
  )
}

export function ErrorEstadoAnalitica({
  mensaje,
  reintentar,
}: {
  mensaje: string
  reintentar: () => void
}) {
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

export function EncabezadoSeccion({
  id,
  eyebrow,
  titulo,
}: {
  id?: string
  eyebrow: string
  titulo: string
}) {
  return (
    <div className="flex items-center gap-3">
      <span className={cn('h-6 w-1.5 rounded-full', paletaSaberPro.separador)} aria-hidden="true" />
      <div>
        <p className={cn('text-[11px] font-semibold uppercase tracking-[0.2em]', paletaSaberPro.apoyoTitulo)}>
          {eyebrow}
        </p>
        <h2 id={id} className={cn('mt-0.5 text-[22px] font-bold tracking-tight', paletaSaberPro.titulo)}>
          {titulo}
        </h2>
      </div>
    </div>
  )
}

export function TarjetaMetrica({
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

// Indicadores generales. `institucional` añade cursos y carreras al detalle,
// que solo tienen sentido cuando el conjunto consultado es consolidado.
export function ResumenMetricas({
  resumen,
  institucional = false,
}: {
  resumen: ResumenAnaliticaSaberPro
  institucional?: boolean
}) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <TarjetaMetrica
        icono={<BarChart3 className="h-3 w-3" />}
        etiqueta="Promedio"
        valor={resumen.promedio_calificacion.toFixed(2)}
        detalle="calificación / 5.00"
      />
      <TarjetaMetrica
        icono={<Target className="h-3 w-3" />}
        etiqueta="Acierto"
        valor={`${resumen.porcentaje_acierto.toFixed(1)}%`}
        detalle={`${resumen.aciertos} de ${resumen.total_preguntas} ítems`}
      />
      <TarjetaMetrica
        icono={<BarChart3 className="h-3 w-3" />}
        etiqueta="Aprobados"
        valor={`${resumen.tasa_aprobacion.toFixed(1)}%`}
        detalle={`${resumen.aprobados} de ${resumen.total_intentos} intentos`}
      />
      <TarjetaMetrica
        icono={<BarChart3 className="h-3 w-3" />}
        etiqueta={institucional ? 'Cobertura' : 'Participación'}
        valor={String(resumen.total_estudiantes)}
        detalle={
          institucional
            ? `${resumen.total_cursos} cursos · ${resumen.total_programas} carreras`
            : `${resumen.total_intentos} intentos elegibles`
        }
      />
    </div>
  )
}

export function DistribucionCalificaciones({
  datos,
}: {
  datos: DistribucionCalificacionAnaliticaSaberPro[]
}) {
  const hayDatos = datos.some((franja) => franja.cantidad > 0)
  return (
    <div className={cn('rounded-2xl border p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>Distribución de calificaciones</p>
      {!hayDatos ? (
        <p className={cn('mt-3 text-xs', paletaSaberPro.apoyo)}>Aún no hay intentos calificados.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {datos.map((franja) => (
            <li key={franja.rango}>
              <div className="flex items-center justify-between gap-3">
                <span className={cn('text-xs font-semibold', paletaSaberPro.texto)}>
                  {franja.rango}
                </span>
                <span className={cn('text-[11px]', paletaSaberPro.apoyo)}>
                  {franja.cantidad} · {franja.porcentaje.toFixed(1)}%
                </span>
              </div>
              <div className={cn('mt-1 h-2 overflow-hidden rounded-full', paletaSaberPro.esqueleto)}>
                <div
                  className={cn('h-full rounded-full', paletaSaberPro.separador)}
                  style={{ width: `${Math.min(100, Math.max(0, franja.porcentaje))}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function ListaFocosBajos({ focos }: { focos: FocoBajoAnaliticaSaberPro[] }) {
  return (
    <div className={cn('rounded-2xl border p-5', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>Focos de refuerzo</p>
      {focos.length === 0 ? (
        <p className={cn('mt-3 text-xs', paletaSaberPro.apoyo)}>
          No hay suficientes ítems evaluados para identificar focos.
        </p>
      ) : (
        <ol className="mt-4 space-y-3">
          {focos.map((foco, indice) => (
            <li key={`${foco.tipo}-${foco.id}`} className="flex items-start gap-3">
              <span
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold',
                  paletaSaberPro.numeracionPaso
                )}
              >
                {indice + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p className={cn('truncate text-xs font-semibold', paletaSaberPro.titulo)}>
                  {foco.nombre}
                </p>
                <p className={cn('text-[10px] uppercase tracking-[0.08em]', paletaSaberPro.apoyo)}>
                  {foco.tipo} · {foco.total_preguntas} ítems
                </p>
              </div>
              <span className={cn('shrink-0 text-sm font-black', paletaSaberPro.accion)}>
                {foco.porcentaje_acierto.toFixed(1)}%
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

// Color del indicador según el nivel de logro, usando solo la paleta
// institucional: navy para logro alto, dorado para medio y naranja de acción
// para los focos que requieren refuerzo prioritario.
function colorPorcentaje(porcentaje: number) {
  if (porcentaje >= 70) return paletaSaberPro.titulo
  if (porcentaje >= 50) return paletaSaberPro.apoyoTitulo
  return paletaSaberPro.accion
}

export function TablaDesglose({
  titulo,
  descripcion,
  filas,
  vacio,
}: {
  titulo: string
  descripcion?: string
  filas: FilaDesgloseAnalitica[]
  vacio: string
}) {
  return (
    <div className={cn('overflow-hidden rounded-2xl border', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <div className="flex flex-wrap items-baseline justify-between gap-2 px-5 pt-4">
        <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>{titulo}</p>
        {descripcion && <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>{descripcion}</p>}
      </div>

      {filas.length === 0 ? (
        <p className={cn('px-5 pb-5 pt-3 text-xs', paletaSaberPro.apoyo)}>{vacio}</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <Table className="bg-transparent [&_td]:text-[#2c3e50] dark:[&_td]:text-[#CFC9BA]">
            <TableHeader>
              <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
                <TableHead className={paletaSaberPro.apoyoTitulo}>Criterio</TableHead>
                <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Aciertos</TableHead>
                <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Ítems</TableHead>
                <TableHead className={cn('text-right', paletaSaberPro.apoyoTitulo)}>% acierto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filas.map((fila) => (
                <TableRow
                  key={fila.clave}
                  className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]"
                >
                  <TableCell className="min-w-48 py-3">
                    <p className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>{fila.nombre}</p>
                    {fila.detalle && (
                      <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>{fila.detalle}</p>
                    )}
                  </TableCell>
                  <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                    {fila.aciertos}
                  </TableCell>
                  <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                    {fila.total_preguntas}
                  </TableCell>
                  <TableCell className="py-3 text-right">
                    <span className={cn('text-sm font-black', colorPorcentaje(fila.porcentaje_acierto))}>
                      {fila.porcentaje_acierto.toFixed(1)}%
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

export function TablaComparativa({
  titulo,
  filas,
  vacio,
}: {
  titulo: string
  filas: FilaComparativaAnalitica[]
  vacio: string
}) {
  return (
    <div className={cn('overflow-hidden rounded-2xl border', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <div className="px-5 pt-4">
        <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>{titulo}</p>
      </div>

      {filas.length === 0 ? (
        <p className={cn('px-5 pb-5 pt-3 text-xs', paletaSaberPro.apoyo)}>{vacio}</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <Table className="bg-transparent [&_td]:text-[#2c3e50] dark:[&_td]:text-[#CFC9BA]">
            <TableHeader>
              <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
                <TableHead className={paletaSaberPro.apoyoTitulo}>Grupo</TableHead>
                <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Estudiantes</TableHead>
                <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Intentos</TableHead>
                <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Promedio</TableHead>
                <TableHead className={cn('text-right', paletaSaberPro.apoyoTitulo)}>% acierto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filas.map((fila) => (
                <TableRow
                  key={fila.clave}
                  className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]"
                >
                  <TableCell className="min-w-48 py-3">
                    <p className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>{fila.nombre}</p>
                    {fila.detalle && (
                      <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>{fila.detalle}</p>
                    )}
                  </TableCell>
                  <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                    {fila.total_estudiantes}
                  </TableCell>
                  <TableCell className={cn('py-3 text-center text-xs', paletaSaberPro.texto)}>
                    {fila.total_intentos}
                  </TableCell>
                  <TableCell className={cn('py-3 text-center text-xs font-semibold', paletaSaberPro.texto)}>
                    {fila.promedio_calificacion.toFixed(2)}
                  </TableCell>
                  <TableCell className="py-3 text-right">
                    <span className={cn('text-sm font-black', colorPorcentaje(fila.porcentaje_acierto))}>
                      {fila.porcentaje_acierto.toFixed(1)}%
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
