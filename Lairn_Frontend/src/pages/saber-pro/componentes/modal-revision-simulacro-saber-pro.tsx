import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, ClipboardCheck, Loader2, Save } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import api from '@/services/api'
import { cn } from '@/lib/utils'
import type {
  DatosRevisionPresentacionSaberPro,
  DetalleRevisionSaberPro,
  ResultadoEstudianteSimulacroSaberPro,
  ResultadosSimulacroSaberPro,
  SimulacroSaberPro,
} from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

interface Props {
  abierta: boolean
  cursoId: number
  simulacro: SimulacroSaberPro | null
  onCerrar: () => void
  onCambio?: () => void
}

function mensajeDeError(error: unknown): string {
  const datos = (error as { response?: { data?: Record<string, unknown> } }).response?.data
  if (!datos) return 'No se pudo completar la operación.'
  if (typeof datos.detalle === 'string') return datos.detalle
  return 'Revisa la calificación: debe estar entre 0.0 y 5.0.'
}

export function ModalRevisionSimulacroSaberPro({
  abierta,
  cursoId,
  simulacro,
  onCerrar,
  onCambio,
}: Props) {
  const [lista, setLista] = useState<ResultadoEstudianteSimulacroSaberPro[]>([])
  const [detalle, setDetalle] = useState<DetalleRevisionSaberPro | null>(null)
  const [nota, setNota] = useState('')
  const [retroalimentacion, setRetroalimentacion] = useState('')
  const [cargando, setCargando] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const base = simulacro
    ? `/saber-pro/docente/cursos/${cursoId}/simulacros/${simulacro.id}/resultados/`
    : ''

  const cargarLista = useCallback(async () => {
    if (!base) return
    setCargando(true)
    try {
      const { data } = await api.get<ResultadosSimulacroSaberPro>(base, {
        params: { intentos: 'todos' },
      })
      setLista(data.resultados.filter((r) => r.requiere_revision))
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setCargando(false)
    }
  }, [base])

  useEffect(() => {
    if (abierta) {
      setDetalle(null)
      void cargarLista()
    }
  }, [abierta, cargarLista])

  const abrirDetalle = async (id: number) => {
    setCargando(true)
    try {
      const { data } = await api.get<DetalleRevisionSaberPro>(`${base}${id}/revision/`)
      setDetalle(data)
      setNota(data.calificacion_docente?.toString() ?? '')
      setRetroalimentacion(data.retroalimentacion ?? '')
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setCargando(false)
    }
  }

  const guardar = async () => {
    if (!detalle) return
    const valor = Number(nota.replace(',', '.'))
    if (!nota.trim() || Number.isNaN(valor) || valor < 0 || valor > 5) {
      toast.error('La nota debe estar entre 0.0 y 5.0.')
      return
    }
    const payload: DatosRevisionPresentacionSaberPro = {
      calificacion: Math.round(valor * 10) / 10,
      retroalimentacion,
    }
    setGuardando(true)
    try {
      await api.post(`${base}${detalle.presentacion_id}/revision/`, payload)
      toast.success('Calificación guardada')
      setDetalle(null)
      await cargarLista()
      onCambio?.()
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setGuardando(false)
    }
  }

  const sinResponder = detalle ? Math.max(0, detalle.total_consignas - detalle.respuestas.length) : 0

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && onCerrar()}>
      <DialogContent
        className={cn(
          'flex max-h-[92vh] max-w-[calc(100%-1.5rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-3xl',
          paletaSaberPro.superficie
        )}
      >
        <DialogHeader className="shrink-0 gap-1 border-b p-4 text-left sm:p-6">
          <DialogTitle className={cn('pr-6 text-lg sm:text-xl', paletaSaberPro.titulo)}>
            Revisión: {simulacro?.titulo || 'Simulacro'}
          </DialogTitle>
          <DialogDescription className={cn('text-xs sm:text-sm', paletaSaberPro.texto)}>
            Cada intento se califica por separado con una nota de 0.0 a 5.0 para el examen completo.
            La nota final del estudiante es la de su intento más alto.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
          {cargando && (
            <div className="flex justify-center py-10">
              <Loader2 className={cn('h-7 w-7 animate-spin', paletaSaberPro.accion)} />
            </div>
          )}

          {!cargando && !detalle && lista.length === 0 && (
            <p className={cn('py-10 text-center text-sm', paletaSaberPro.texto)}>
              Aún no hay intentos finalizados con respuestas escritas.
            </p>
          )}

          {!cargando && !detalle && lista.length > 0 && (
            <ul className="space-y-3">
              {lista.map((item) => (
                <li
                  key={item.id}
                  className={cn(
                    'flex flex-col gap-3 rounded-xl border p-3 sm:flex-row sm:items-center sm:justify-between sm:p-4',
                    paletaSaberPro.borde
                  )}
                >
                  <div className="min-w-0">
                    <p className={cn('truncate text-sm font-semibold', paletaSaberPro.titulo)}>
                      {item.estudiante.nombre_completo || 'Estudiante sin nombre'}
                    </p>
                    <p className={cn('break-all text-xs', paletaSaberPro.apoyo)}>
                      {item.estudiante.email}
                    </p>
                    <p className={cn('mt-0.5 text-[11px] font-semibold', paletaSaberPro.titulo)}>
                      Intento {item.intento}
                      {!item.revision_pendiente && (
                        <span className={cn('ml-2 font-normal', paletaSaberPro.apoyo)}>
                          Nota {item.calificacion.toFixed(1)} / 5.0
                        </span>
                      )}
                    </p>
                  </div>

                  <div className="flex items-center justify-between gap-3 sm:justify-end">
                    <Badge
                      variant="outline"
                      className={cn(
                        'shrink-0 text-[10px]',
                        item.revision_pendiente
                          ? 'border-[#e8740e]/40 text-[#e8740e] dark:border-[#F29A52]/50 dark:text-[#F29A52]'
                          : paletaSaberPro.badge
                      )}
                    >
                      {item.revision_pendiente ? 'Pendiente' : 'Calificado'}
                    </Badge>
                    <Button
                      type="button"
                      size="sm"
                      className={cn('h-9 flex-1 gap-1.5 sm:flex-none', paletaSaberPro.botonAccion)}
                      onClick={() => void abrirDetalle(item.id)}
                    >
                      <ClipboardCheck className="h-4 w-4" />
                      {item.revision_pendiente ? 'Revisar' : 'Ver / editar'}
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {!cargando && detalle && (
            <div className="space-y-5">
              <div>
                <p className={cn('text-sm font-bold sm:text-base', paletaSaberPro.titulo)}>
                  {detalle.estudiante_nombre}
                </p>
                <p className={cn('text-xs', paletaSaberPro.apoyo)}>Intento {detalle.intento}</p>
              </div>

              {sinResponder > 0 && (
                <p className="rounded-lg border border-[#e8740e]/40 bg-[#e8740e]/5 px-3 py-2 text-xs text-[#e8740e] dark:border-[#F29A52]/50 dark:bg-[#F29A52]/10 dark:text-[#F29A52]">
                  El estudiante no respondió {sinResponder} de {detalle.total_consignas} consigna
                  {detalle.total_consignas === 1 ? '' : 's'}.
                </p>
              )}

              {detalle.respuestas.length === 0 && (
                <p className={cn('rounded-xl border p-4 text-sm', paletaSaberPro.borde, paletaSaberPro.texto)}>
                  Este intento no tiene respuestas escritas.
                </p>
              )}

              {detalle.respuestas.map((r) => {
                const excede = r.limite_palabras != null && r.palabras > r.limite_palabras
                return (
                  <section
                    key={r.id}
                    className={cn('space-y-3 rounded-xl border p-3 sm:p-4', paletaSaberPro.borde)}
                  >
                    <p
                      className={cn(
                        'text-xs font-semibold uppercase tracking-[0.1em]',
                        paletaSaberPro.apoyoTitulo
                      )}
                    >
                      Consigna {r.orden}
                      {r.tema ? ` · ${r.tema}` : ''}
                    </p>
                    {r.contexto && (
                      <p className={cn('whitespace-pre-wrap break-words text-xs', paletaSaberPro.apoyo)}>
                        {r.contexto}
                      </p>
                    )}
                    <p className={cn('break-words text-sm font-medium', paletaSaberPro.titulo)}>
                      {r.enunciado}
                    </p>

                    <div>
                      <p className={cn('mb-1 text-[11px] font-semibold', paletaSaberPro.titulo)}>
                        Respuesta del estudiante
                      </p>
                      <div
                        className={cn(
                          'max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border p-3 text-sm sm:max-h-80',
                          paletaSaberPro.bandaAlterna,
                          paletaSaberPro.borde,
                          paletaSaberPro.texto
                        )}
                      >
                        {r.texto || 'Sin texto.'}
                      </div>
                      <p
                        className={cn(
                          'mt-1 text-right text-[11px]',
                          excede ? 'font-semibold text-[#b8432a]' : paletaSaberPro.apoyo
                        )}
                      >
                        {r.palabras}
                        {r.limite_palabras != null ? ` / ${r.limite_palabras}` : ''} palabras
                      </p>
                    </div>
                  </section>
                )
              })}

              <section
                className={cn(
                  'space-y-3 rounded-xl border-2 p-3 sm:p-4',
                  'border-[#e8740e]/50 dark:border-[#F29A52]/60',
                  paletaSaberPro.bandaAlterna
                )}
              >
                <p className={cn('text-sm font-bold', paletaSaberPro.titulo)}>
                  Calificación del intento completo
                </p>
                <div className="grid gap-3 sm:grid-cols-[140px_1fr]">
                  <label className={cn('space-y-1 text-xs font-semibold', paletaSaberPro.titulo)}>
                    Nota (0.0 – 5.0)
                    <input
                      type="number"
                      inputMode="decimal"
                      min={0}
                      max={5}
                      step={0.1}
                      value={nota}
                      onChange={(e) => setNota(e.target.value)}
                      className="h-10 w-full rounded-md border bg-white px-3 text-sm dark:bg-[#172A45]"
                    />
                  </label>
                  <label className={cn('space-y-1 text-xs font-semibold', paletaSaberPro.titulo)}>
                    Retroalimentación para el estudiante
                    <Textarea
                      maxLength={2000}
                      value={retroalimentacion}
                      onChange={(e) => setRetroalimentacion(e.target.value)}
                      className="min-h-28 bg-white text-sm dark:bg-[#172A45]"
                    />
                  </label>
                </div>
                {detalle.revisada_por && (
                  <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>
                    Última revisión de {detalle.revisada_por.nombre_completo}
                  </p>
                )}
              </section>
            </div>
          )}
        </div>

        {!cargando && detalle && (
          <div
            className={cn(
              'flex shrink-0 flex-col-reverse gap-2 border-t p-3 sm:flex-row sm:justify-between sm:p-4',
              paletaSaberPro.bandaAlterna
            )}
          >
            <Button
              type="button"
              variant="outline"
              className={cn('gap-1.5', paletaSaberPro.botonNeutro)}
              onClick={() => setDetalle(null)}
              disabled={guardando}
            >
              <ArrowLeft className="h-4 w-4" /> Volver al listado
            </Button>
            <Button
              type="button"
              className={cn('gap-2', paletaSaberPro.botonAccion)}
              disabled={guardando}
              onClick={() => void guardar()}
            >
              {guardando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Guardar calificación
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}