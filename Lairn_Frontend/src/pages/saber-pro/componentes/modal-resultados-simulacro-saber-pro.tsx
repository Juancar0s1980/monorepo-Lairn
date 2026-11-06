// Modal de calificaciones de un simulacro Saber Pro (HU-24).
//
// El docente propietario del curso consulta los intentos finalizados de sus
// estudiantes. La calificación se muestra en escala 0.0-5.0; el backend
// conserva además el puntaje interno 0-100 y los contadores de acierto.

import type { ReactNode } from 'react'
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ClipboardList,
  GraduationCap,
  Loader2,
  Repeat,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
import { useResultadosSimulacroSaberPro } from '@/hooks/use-resultados-simulacro-saber-pro'
import type {
  ResultadoEstudianteSimulacroSaberPro,
  SimulacroSaberPro,
} from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

interface ModalResultadosSimulacroSaberProProps {
  abierta: boolean
  cursoId: number
  simulacro: SimulacroSaberPro | null
  onCerrar: () => void
}

function formatearFecha(fecha: string | null): string {
  if (!fecha) return 'Sin registrar'
  return new Date(fecha).toLocaleString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
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
    <div className={cn('rounded-xl border p-3', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <p className={cn('flex items-center gap-1.5 text-[10px] uppercase tracking-[0.08em]', paletaSaberPro.apoyo)}>
        {icono} {etiqueta}
      </p>
      <p className={cn('mt-1 text-xl font-bold', paletaSaberPro.titulo)}>{valor}</p>
      <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>{detalle}</p>
    </div>
  )
}

function FilaResultado({ resultado }: { resultado: ResultadoEstudianteSimulacroSaberPro }) {
  const pendiente = resultado.revision_pendiente
  return (
    <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
      <TableCell className="min-w-52 py-3">
        <p className={cn('font-semibold', paletaSaberPro.titulo)}>
          {resultado.estudiante.nombre_completo || 'Estudiante sin nombre'}
        </p>
        <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>{resultado.estudiante.email}</p>
                {resultado.intentos_pendientes > 0 && (
          <Badge
            variant="outline"
            className="mt-1 border-[#e8740e]/40 text-[10px] text-[#e8740e] dark:border-[#F29A52]/50 dark:text-[#F29A52]"
          >
            {resultado.intentos_pendientes} intento{resultado.intentos_pendientes === 1 ? '' : 's'}{' '}
            por revisar
          </Badge>
        )}
      </TableCell>
      <TableCell className={cn('py-3 text-center font-semibold', paletaSaberPro.texto)}>
        {resultado.intento}
      </TableCell>
      <TableCell className="py-3 text-center">
        {pendiente ? (
          <p className="text-sm font-semibold text-[#e8740e] dark:text-[#F29A52]">Pendiente</p>
        ) : (
          <>
            <p
              className={cn(
                'text-lg font-black',
                resultado.aprobado
                  ? 'text-[#1e3a5f] dark:text-[#E3C063]'
                  : 'text-[#b8432a] dark:text-[#F29A52]'
              )}
            >
              {resultado.calificacion.toFixed(2)}
            </p>
            <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>/ 5.00</p>
          </>
        )}
      </TableCell>
      <TableCell className="py-3 text-center">
        <p className={cn('text-sm font-semibold', paletaSaberPro.titulo)}>
          {resultado.correctas}/{resultado.total_evaluables}
        </p>
        <p className={cn('text-[10px]', paletaSaberPro.apoyo)}>
          {pendiente ? 'solo ítems automáticos' : `${resultado.puntaje.toFixed(1)}% de acierto`}
        </p>
      </TableCell>
      <TableCell className={cn('min-w-40 py-3 text-xs', paletaSaberPro.texto)}>
        {formatearFecha(resultado.finalizada_en)}
        <p className={cn('mt-0.5 text-[10px]', paletaSaberPro.apoyo)}>
          {resultado.contenidos_respondidos}/{resultado.total_preguntas} bloques respondidos
        </p>
      </TableCell>
    </TableRow>
  )
}

export function ModalResultadosSimulacroSaberPro({
  abierta,
  cursoId,
  simulacro,
  onCerrar,
}: ModalResultadosSimulacroSaberProProps) {
  const { datos, cargando, error, recargar } = useResultadosSimulacroSaberPro(
    cursoId,
    simulacro?.id ?? null,
    abierta && Boolean(simulacro)
  )

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && onCerrar()}>
      <DialogContent className="max-h-[92vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-5xl">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipGold}`}>
              <GraduationCap className="h-6 w-6" />
            </span>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {simulacro?.area.nombre ?? 'Saber Pro'} · Calificaciones
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>
              Calificaciones del simulacro
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              {simulacro?.titulo || 'Simulacro sin título'}. Se muestra la mejor calificación de
              cada estudiante entre sus intentos finalizados, sobre 5.0.
            </DialogDescription>
          </DialogHeader>
        </div>

        <div className={`space-y-5 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
          {cargando && (
            <div className="flex min-h-40 flex-col items-center justify-center gap-3">
              <Loader2 className={cn('h-8 w-8 animate-spin', paletaSaberPro.accion)} />
              <p className={cn('text-sm', paletaSaberPro.texto)}>Cargando calificaciones...</p>
            </div>
          )}

          {!cargando && error && (
            <div className={cn('flex flex-col items-center rounded-2xl border p-8 text-center', paletaSaberPro.superficie, paletaSaberPro.borde)}>
              <span className={cn('flex h-12 w-12 items-center justify-center rounded-full', paletaSaberPro.chipAccion)}>
                <AlertCircle className="h-6 w-6" />
              </span>
              <p className={cn('mt-3 text-sm font-medium', paletaSaberPro.titulo)}>{error}</p>
              <Button type="button" className={cn('mt-4', paletaSaberPro.botonNeutro)} onClick={() => void recargar()}>
                Reintentar
              </Button>
            </div>
          )}

          {!cargando && !error && datos && (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <DatoResumen
                  icono={<BarChart3 className="h-3 w-3" />}
                  etiqueta="Promedio"
                  valor={datos.resumen.promedio_calificacion.toFixed(2)}
                  detalle="de las mejores notas"
                />
                <DatoResumen
                  icono={<ClipboardList className="h-3 w-3" />}
                  etiqueta="Intentos"
                  valor={String(datos.resumen.total_intentos)}
                  detalle={`${datos.resumen.total_estudiantes} estudiantes`}
                />
                <DatoResumen
                  icono={<Repeat className="h-3 w-3" />}
                  etiqueta="Límite"
                  valor={String(datos.intentos_maximos)}
                  detalle="intentos por estudiante"
                />
                <DatoResumen
                  icono={<CheckCircle2 className="h-3 w-3" />}
                  etiqueta="Aprobados"
                  valor={String(datos.resumen.aprobados)}
                  detalle="con nota mayor o igual a 3.00"
                />
              </div>

              {datos.resumen.requieren_revision > 0 && (
                <p className="rounded-lg border border-[#e8740e]/40 bg-[#e8740e]/5 px-3 py-2 text-xs text-[#e8740e] dark:border-[#F29A52]/50 dark:bg-[#F29A52]/10 dark:text-[#F29A52]">
                  Hay {datos.resumen.requieren_revision} intento
                  {datos.resumen.requieren_revision === 1 ? '' : 's'} pendiente
                  {datos.resumen.requieren_revision === 1 ? '' : 's'} de revisión. Califícalos con el botón
                  «Revisar respuestas» de la tarjeta del simulacro. El promedio y los aprobados solo
                  cuentan estudiantes con al menos un intento calificado.
                </p>
              )}

              {datos.resultados.length === 0 ? (
                <div className={cn('flex flex-col items-center rounded-2xl border border-dashed p-10 text-center', paletaSaberPro.superficie, paletaSaberPro.borde)}>
                  <span className={cn('flex h-14 w-14 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
                    <GraduationCap className="h-7 w-7" />
                  </span>
                  <p className={cn('mt-3 text-base font-bold', paletaSaberPro.titulo)}>
                    Aún no hay intentos finalizados
                  </p>
                  <p className={cn('mt-1 max-w-md text-sm', paletaSaberPro.texto)}>
                    Las calificaciones aparecerán aquí cuando tus estudiantes terminen el simulacro.
                  </p>
                </div>
              ) : (
                <Table className="bg-transparent [&_td]:text-[#2c3e50] dark:[&_td]:text-[#CFC9BA]">
                  <TableHeader>
                    <TableRow className="border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]">
                      <TableHead className={paletaSaberPro.apoyoTitulo}>Estudiante</TableHead>
                      <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Mejor intento</TableHead>
                      <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Calificación</TableHead>
                      <TableHead className={cn('text-center', paletaSaberPro.apoyoTitulo)}>Aciertos</TableHead>
                      <TableHead className={paletaSaberPro.apoyoTitulo}>Finalización</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {datos.resultados.map((resultado) => (
                      <FilaResultado key={resultado.id} resultado={resultado} />
                    ))}
                  </TableBody>
                </Table>
              )}
            </>
          )}

          <div className={cn('flex justify-end border-t pt-4', paletaSaberPro.borde)}>
            <Button type="button" className={paletaSaberPro.botonNeutro} onClick={onCerrar}>
              Cerrar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}