// Campana de notificaciones del docente para los simulacros Saber Pro.
//
// Se muestra en las cabeceras de las vistas del docente dentro del módulo Saber
// Pro (no en el header global del sistema). Mientras el docente navega por el
// módulo, este componente consulta cada 10 s las solicitudes de desbloqueo
// pendientes de sus cursos. El contador se muestra junto a la campana y el panel
// lateral permite aprobar el intento de un estudiante, rechazarlo para que se
// envíe automáticamente o rechazarlo y anularlo con nota 0 y sin nuevos intentos,
// sin salir de la página en la que está.

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Ban,
  Bell,
  Check,
  CheckCircle2,
  Loader2,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import api from '@/services/api'
import { cn } from '@/lib/utils'
import type {
  ListaSolicitudesDesbloqueo,
  SolicitudDesbloqueoDocente,
} from '@/types/saber-pro'
import { paletaSaberPro } from '@/pages/saber-pro/utilidades'

const INTERVALO_MS = 10_000

const ETIQUETAS_MOTIVO: Record<string, string> = {
  cambio_pestana: 'Cambio de pestaña',
  pantalla_completa: 'Salió de pantalla completa',
  perdida_foco: 'Pérdida de foco',
}

function mensajeDeError(error: unknown): string {
  const axiosErr = error as { response?: { data?: Record<string, unknown> } }
  const data = axiosErr.response?.data
  if (data) {
    if (typeof data.detalle === 'string') return data.detalle
    const mensajes = Object.values(data)
      .flatMap((valor) => (Array.isArray(valor) ? valor : [valor]))
      .filter((valor): valor is string => typeof valor === 'string')
    if (mensajes.length > 0) return mensajes.join('. ')
  }
  return 'No se pudieron gestionar las solicitudes de desbloqueo.'
}

function horaSolicitud(fechaIso: string): string {
  return new Date(fechaIso).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function inicial(nombre: string): string {
  return nombre.trim().charAt(0).toUpperCase() || '?'
}

export function CampanaDesbloqueosSaberPro() {
  const [abierto, setAbierto] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [solicitudes, setSolicitudes] = useState<SolicitudDesbloqueoDocente[]>([])
  const [aprobandoId, setAprobandoId] = useState<number | null>(null)
  const [rechazandoId, setRechazandoId] = useState<number | null>(null)
  const [anulandoId, setAnulandoId] = useState<number | null>(null)
  const [solicitudARechazar, setSolicitudARechazar] =
    useState<SolicitudDesbloqueoDocente | null>(null)
  const [solicitudAAnular, setSolicitudAAnular] =
    useState<SolicitudDesbloqueoDocente | null>(null)
  const peticionRef = useRef(0)

  const cargar = useCallback(async () => {
    const peticion = ++peticionRef.current
    try {
      const { data } = await api.get<ListaSolicitudesDesbloqueo>(
        '/saber-pro/docente/solicitudes-desbloqueo/'
      )
      // Descarta respuestas viejas si ya se disparó una consulta más reciente
      // (por ejemplo, justo después de aprobar un desbloqueo).
      if (peticion !== peticionRef.current) return
      setSolicitudes(data.solicitudes)
      setError(null)
    } catch (err: unknown) {
      if (peticion !== peticionRef.current) return
      setError(mensajeDeError(err))
    } finally {
      if (peticion === peticionRef.current) setCargando(false)
    }
  }, [])

  useEffect(() => {
    // La primera consulta se difiere para no encadenar renders sincrónicos en
    // el montaje; el intervalo mantiene la campana actualizada en segundo plano.
    const inicial = window.setTimeout(() => void cargar(), 0)
    const intervalo = window.setInterval(() => void cargar(), INTERVALO_MS)
    return () => {
      window.clearTimeout(inicial)
      window.clearInterval(intervalo)
    }
  }, [cargar])

  const aprobar = useCallback(
    async (solicitud: SolicitudDesbloqueoDocente) => {
      setAprobandoId(solicitud.id)
      try {
        await api.post(
          `/saber-pro/docente/solicitudes-desbloqueo/${solicitud.id}/aprobar/`
        )
        toast.success(
          `Desbloqueaste el intento de ${solicitud.estudiante.nombre_completo}.`
        )
        await cargar()
      } catch (err: unknown) {
        toast.error(mensajeDeError(err))
      } finally {
        setAprobandoId(null)
      }
    },
    [cargar]
  )

  const rechazar = useCallback(
    async (solicitud: SolicitudDesbloqueoDocente) => {
      setRechazandoId(solicitud.id)
      try {
        await api.post(
          `/saber-pro/docente/solicitudes-desbloqueo/${solicitud.id}/rechazar/`
        )
        toast.success(
          `Rechazaste el desbloqueo de ${solicitud.estudiante.nombre_completo}. Su intento se envió automáticamente.`
        )
        setSolicitudARechazar(null)
        await cargar()
      } catch (err: unknown) {
        toast.error(mensajeDeError(err))
      } finally {
        setRechazandoId(null)
      }
    },
    [cargar]
  )

  const rechazarYAnular = useCallback(
    async (solicitud: SolicitudDesbloqueoDocente) => {
      setAnulandoId(solicitud.id)
      try {
        await api.post(
          `/saber-pro/docente/solicitudes-desbloqueo/${solicitud.id}/rechazar-anular/`
        )
        toast.success(
          `Anulaste el simulacro de ${solicitud.estudiante.nombre_completo}. Su calificación queda en 0 y no podrá volver a presentarlo.`
        )
        setSolicitudAAnular(null)
        await cargar()
      } catch (err: unknown) {
        toast.error(mensajeDeError(err))
      } finally {
        setAnulandoId(null)
      }
    },
    [cargar]
  )

  const total = solicitudes.length

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="relative text-muted-foreground hover:text-foreground"
        onClick={() => setAbierto(true)}
        aria-label={
          total > 0
            ? `Solicitudes de desbloqueo: ${total} pendientes`
            : 'Solicitudes de desbloqueo'
        }
      >
        <Bell className="h-5 w-5" />
        {total > 0 && (
          <span
            className={cn(
              'absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-bold',
              'bg-[#e8740e] text-white dark:bg-[#F29A52] dark:text-[#172A45]'
            )}
          >
            {total > 9 ? '9+' : total}
          </span>
        )}
      </Button>

      <Sheet
        open={abierto}
        onOpenChange={(nuevo) => {
          setAbierto(nuevo)
          if (nuevo) void cargar()
        }}
      >
        <SheetContent
          side="right"
          className={cn('w-full sm:max-w-md', paletaSaberPro.superficie)}
        >
          <SheetHeader className="gap-1 pb-4">
            <div className="flex items-start justify-between gap-3 pr-8">
              <div>
                <SheetTitle className={cn('text-xl', paletaSaberPro.titulo)}>
                  Desbloqueos de simulacro
                </SheetTitle>
                <SheetDescription className={cn('text-sm', paletaSaberPro.apoyo)}>
                  Desbloquea el intento del estudiante, recházalo para enviarlo o
                  recházalo y anúlalo con nota 0 y sin nuevos intentos.
                </SheetDescription>
              </div>
              <Button
                variant="outline"
                size="icon"
                className={cn('shrink-0', paletaSaberPro.botonNeutro)}
                onClick={() => void cargar()}
                aria-label="Actualizar solicitudes"
                disabled={cargando}
              >
                <RefreshCw className={cn('h-4 w-4', cargando && 'animate-spin')} />
              </Button>
            </div>
          </SheetHeader>

          <div className="flex h-[calc(100vh-9rem)] flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto pr-1">
              {cargando && total === 0 && (
                <div className="flex flex-col items-center justify-center gap-3 py-16">
                  <Loader2 className={cn('h-7 w-7 animate-spin', paletaSaberPro.accion)} />
                  <p className={cn('text-sm', paletaSaberPro.apoyo)}>
                    Consultando solicitudes...
                  </p>
                </div>
              )}

              {!cargando && error && total === 0 && (
                <div
                  className={cn(
                    'rounded-xl border p-4 text-sm',
                    paletaSaberPro.borde,
                    paletaSaberPro.bandaAlterna
                  )}
                >
                  <p className={cn('font-semibold', paletaSaberPro.titulo)}>
                    No se pudieron cargar las solicitudes
                  </p>
                  <p className={cn('mt-1 text-xs', paletaSaberPro.apoyo)}>{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className={cn('mt-3 gap-2', paletaSaberPro.botonNeutro)}
                    onClick={() => void cargar()}
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    Reintentar
                  </Button>
                </div>
              )}

              {!cargando && total === 0 && !error && (
                <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                  <span
                    className={cn(
                      'flex h-14 w-14 items-center justify-center rounded-full',
                      paletaSaberPro.iconoChip
                    )}
                  >
                    <ShieldCheck className="h-7 w-7" />
                  </span>
                  <div>
                    <p className={cn('font-semibold', paletaSaberPro.titulo)}>
                      Todo bajo control
                    </p>
                    <p className={cn('mt-1 text-sm', paletaSaberPro.apoyo)}>
                      No hay estudiantes esperando desbloqueo.
                    </p>
                  </div>
                </div>
              )}

              {total > 0 && (
                <ul className="flex flex-col gap-3">
                  {solicitudes.map((solicitud) => {
                    const aprobando = aprobandoId === solicitud.id
                    const rechazando = rechazandoId === solicitud.id
                    const anulando = anulandoId === solicitud.id
                    return (
                      <li
                        key={solicitud.id}
                        className={cn(
                          'rounded-xl border p-3.5',
                          paletaSaberPro.borde,
                          paletaSaberPro.bandaAlterna
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={cn(
                              'flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold',
                              paletaSaberPro.numeracionPaso
                            )}
                          >
                            {inicial(solicitud.estudiante.nombre_completo)}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <p
                                  className={cn(
                                    'truncate text-sm font-semibold',
                                    paletaSaberPro.titulo
                                  )}
                                >
                                  {solicitud.estudiante.nombre_completo}
                                </p>
                                <p
                                  className={cn(
                                    'truncate text-xs',
                                    paletaSaberPro.apoyo
                                  )}
                                >
                                  {solicitud.estudiante.email}
                                </p>
                              </div>
                              <span
                                className={cn(
                                  'shrink-0 text-[11px] font-medium',
                                  paletaSaberPro.apoyo
                                )}
                              >
                                {horaSolicitud(solicitud.creada_en)}
                              </span>
                            </div>

                            <p
                              className={cn(
                                'mt-2 line-clamp-2 text-xs leading-relaxed',
                                paletaSaberPro.texto
                              )}
                            >
                              <span className="font-semibold">
                                {solicitud.simulacro_titulo}
                              </span>
                              {' · '}
                              {solicitud.curso_nombre}
                              {solicitud.area_nombre
                                ? ` · ${solicitud.area_nombre}`
                                : ''}
                            </p>

                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span
                                className={cn(
                                  'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold',
                                  paletaSaberPro.chipAccion
                                )}
                              >
                                <LockKeyhole className="h-3 w-3" />
                                {ETIQUETAS_MOTIVO[solicitud.motivo] ??
                                  'Salida detectada'}
                              </span>
                              <span
                                className={cn(
                                  'rounded-full px-2 py-0.5 text-[10px] font-semibold',
                                  paletaSaberPro.chipGold
                                )}
                              >
                                Intento {solicitud.intento}
                              </span>
                            </div>

                            <div className="mt-3 grid grid-cols-2 gap-2">
                              <Button
                                type="button"
                                size="sm"
                                className={cn('gap-2', paletaSaberPro.botonAccion)}
                                onClick={() => void aprobar(solicitud)}
                                disabled={aprobando || rechazando || anulando}
                              >
                                {aprobando ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Check className="h-4 w-4" />
                                )}
                                {aprobando ? 'Desbloqueando...' : 'Desbloquear'}
                              </Button>
                              <Button
                                type="button"
                                variant="destructive"
                                size="sm"
                                className="gap-2"
                                onClick={() => setSolicitudARechazar(solicitud)}
                                disabled={aprobando || rechazando || anulando}
                              >
                                {rechazando ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <XCircle className="h-4 w-4" />
                                )}
                                {rechazando ? 'Rechazando...' : 'Rechazar'}
                              </Button>
                            </div>

                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              className="mt-2 w-full gap-2 border-[#b8432a]/40 text-[#b8432a] hover:bg-[#b8432a]/10 hover:text-[#b8432a] dark:border-[#F29A52]/40 dark:text-[#F29A52] dark:hover:bg-[#F29A52]/10 dark:hover:text-[#F29A52]"
                              onClick={() => setSolicitudAAnular(solicitud)}
                              disabled={aprobando || rechazando || anulando}
                            >
                              {anulando ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Ban className="h-4 w-4" />
                              )}
                              {anulando ? 'Anulando...' : 'Rechazar y anular'}
                            </Button>
                          </div>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>

            <p
              className={cn(
                'flex items-center justify-center gap-1.5 border-t pt-3 text-[11px]',
                paletaSaberPro.borde,
                paletaSaberPro.apoyo
              )}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Actualización automática cada 10 segundos
            </p>
          </div>
        </SheetContent>
      </Sheet>

      <Dialog
        open={solicitudARechazar !== null}
        onOpenChange={(nuevo) => {
          if (!nuevo && rechazandoId === null) setSolicitudARechazar(null)
        }}
      >
        <DialogContent className={cn('sm:max-w-md', paletaSaberPro.superficie)}>
          <DialogHeader>
            <DialogTitle className={cn('text-lg', paletaSaberPro.titulo)}>
              Rechazar desbloqueo
            </DialogTitle>
            <DialogDescription className={cn('text-sm', paletaSaberPro.texto)}>
              {solicitudARechazar
                ? `El intento ${solicitudARechazar.intento} de ${solicitudARechazar.estudiante.nombre_completo} se enviará automáticamente y no podrá reanudarse. Los demás intentos del simulacro no se ven afectados.`
                : ''}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              className={paletaSaberPro.botonNeutro}
              onClick={() => setSolicitudARechazar(null)}
              disabled={rechazandoId !== null}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="gap-2"
              onClick={() => {
                if (solicitudARechazar) void rechazar(solicitudARechazar)
              }}
              disabled={rechazandoId !== null}
            >
              {rechazandoId !== null ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <XCircle className="h-4 w-4" />
              )}
              Rechazar y enviar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={solicitudAAnular !== null}
        onOpenChange={(nuevo) => {
          if (!nuevo && anulandoId === null) setSolicitudAAnular(null)
        }}
      >
        <DialogContent className={cn('sm:max-w-md', paletaSaberPro.superficie)}>
          <DialogHeader>
            <DialogTitle className={cn('text-lg', paletaSaberPro.titulo)}>
              Rechazar y anular simulacro
            </DialogTitle>
            <DialogDescription className={cn('text-sm', paletaSaberPro.texto)}>
              {solicitudAAnular
                ? `El intento ${solicitudAAnular.intento} de ${solicitudAAnular.estudiante.nombre_completo} quedará con calificación 0 sin importar su avance ni sus respuestas. Tampoco podrá volver a presentar este simulacro, aunque le quedaran intentos disponibles. Esta acción no se puede deshacer.`
                : ''}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              className={paletaSaberPro.botonNeutro}
              onClick={() => setSolicitudAAnular(null)}
              disabled={anulandoId !== null}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="gap-2"
              onClick={() => {
                if (solicitudAAnular) void rechazarYAnular(solicitudAAnular)
              }}
              disabled={anulandoId !== null}
            >
              {anulandoId !== null ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Ban className="h-4 w-4" />
              )}
              Rechazar y anular
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
