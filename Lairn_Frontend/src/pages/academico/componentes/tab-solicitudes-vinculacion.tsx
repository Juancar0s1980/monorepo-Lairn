// Bandeja de solicitudes de vinculación curso ↔ asignatura (HU-01.10), para Administrador y Coordinador.
// Aprobar vincula la asignatura al curso del docente; rechazar exige un motivo que el docente verá.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { AlertTriangle, Check, Inbox, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EstadoSolicitud, SolicitudVinculacion } from '@/types/vinculacion'

const FILTROS: { clave: EstadoSolicitud | 'todas'; texto: string }[] = [
  { clave: 'pendiente', texto: 'Pendientes' },
  { clave: 'aprobada', texto: 'Aprobadas' },
  { clave: 'rechazada', texto: 'Rechazadas' },
  { clave: 'todas', texto: 'Todas' },
]
const fecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' })
const ETIQUETA: Record<EstadoSolicitud, string> = {
  pendiente: 'Pendiente', aprobada: 'Aprobada', rechazada: 'Rechazada', cancelada: 'Cancelada por el docente',
}

export function TabSolicitudesVinculacion({ alCambiarPendientes }: { alCambiarPendientes?: (n: number) => void }) {
  const [filtro, setFiltro] = useState<EstadoSolicitud | 'todas'>('pendiente')
  const [solicitudes, setSolicitudes] = useState<SolicitudVinculacion[] | null>(null)
  const [version, setVersion] = useState(0)
  const [decision, setDecision] = useState<{ s: SolicitudVinculacion; accion: 'aprobar' | 'rechazar' } | null>(null)
  const [respuesta, setRespuesta] = useState('')
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true
    api
      .get<{ pendientes: number; solicitudes: SolicitudVinculacion[] }>(`/evaluacion/vinculacion/solicitudes/?estado=${filtro}`)
      .then((r) => {
        if (!vigente) return
        setSolicitudes(r.data.solicitudes)
        alCambiarPendientes?.(r.data.pendientes)
      })
      .catch(() => vigente && setSolicitudes([]))
    return () => {
      vigente = false
    }
  }, [filtro, version, alCambiarPendientes])

  const resolver = async () => {
    if (!decision) return
    setGuardando(true)
    try {
      await api.post(`/evaluacion/vinculacion/solicitudes/${decision.s.id}/${decision.accion}/`, { respuesta })
      toast.success(decision.accion === 'aprobar' ? 'Curso vinculado a la asignatura' : 'Solicitud rechazada')
      setDecision(null)
      setRespuesta('')
      setVersion((v) => v + 1)
    } catch (err) {
      const d = (err as { response?: { data?: Record<string, unknown> } }).response?.data
      const v = d?.detalle ?? (d ? Object.values(d)[0] : undefined)
      toast.error(Array.isArray(v) ? String(v[0]) : String(v ?? 'No se pudo guardar'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Inbox className="h-4 w-4 text-primary" aria-hidden />
          Solicitudes de vinculación de cursos
        </CardTitle>
        <CardDescription>Los docentes piden vincular su curso a una asignatura de la malla para que cuente en los resultados de aprendizaje.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar por estado">
          {FILTROS.map((f) => (
            <button key={f.clave} type="button" aria-pressed={filtro === f.clave} onClick={() => setFiltro(f.clave)}
              className={cn('rounded-full border px-3 py-1 text-xs transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                filtro === f.clave ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground hover:bg-muted')}>
              {f.texto}
            </button>
          ))}
        </div>
        {solicitudes === null ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-primary" aria-label="Cargando" />
          </div>
        ) : solicitudes.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No hay solicitudes en este estado.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Docente y curso</TableHead>
                  <TableHead>Asignatura solicitada</TableHead>
                  <TableHead className="hidden lg:table-cell">Mensaje</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {solicitudes.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>
                      <span className="block font-medium">{s.docente.nombre}</span>
                      <span className="block text-xs text-muted-foreground">{s.docente.email}</span>
                      <span className="block text-xs">Curso: {s.curso.nombre}</span>
                    </TableCell>
                    <TableCell>
                      <span className="block font-medium">{s.asignatura.codigo} · {s.asignatura.nombre}</span>
                      <span className="block text-xs text-muted-foreground">{s.asignatura.programa.codigo} · {s.asignatura.programa.nombre}</span>
                      {s.estado === 'pendiente' && s.asignatura.curso_vinculado && (
                        <span className="mt-0.5 flex items-center gap-1 text-xs text-warning">
                          <AlertTriangle className="h-3 w-3" aria-hidden />
                          Hoy vinculada a «{s.asignatura.curso_vinculado.nombre}»
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="hidden max-w-xs text-xs text-muted-foreground lg:table-cell">
                      {s.mensaje || '—'}
                      <span className="block">{fecha.format(new Date(s.creada_en))}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{ETIQUETA[s.estado]}</Badge>
                      {s.respuesta && <span className="mt-0.5 block max-w-48 text-xs text-muted-foreground">{s.respuesta}</span>}
                    </TableCell>
                    <TableCell className="text-right">
                      {s.estado === 'pendiente' && (
                        <div className="flex justify-end gap-1">
                          <Button size="sm" onClick={() => setDecision({ s, accion: 'aprobar' })}>
                            <Check className="mr-1 h-3.5 w-3.5" aria-hidden />
                            Aprobar
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => setDecision({ s, accion: 'rechazar' })}>
                            <X className="mr-1 h-3.5 w-3.5" aria-hidden />
                            Rechazar
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      <Dialog open={!!decision} onOpenChange={(v) => !v && setDecision(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{decision?.accion === 'aprobar' ? 'Aprobar vinculación' : 'Rechazar solicitud'}</DialogTitle>
            <DialogDescription>
              {decision && `${decision.s.curso.nombre} → ${decision.s.asignatura.codigo} · ${decision.s.asignatura.nombre}`}
            </DialogDescription>
          </DialogHeader>
          {decision?.accion === 'aprobar' && decision.s.asignatura.curso_vinculado && (
            <p className="rounded-lg border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
              La asignatura dejará de estar vinculada a «{decision.s.asignatura.curso_vinculado.nombre}». Queda registrado.
            </p>
          )}
          <div className="space-y-1">
            <Label htmlFor="vin-respuesta">{decision?.accion === 'rechazar' ? 'Motivo del rechazo *' : 'Nota para el docente (opcional)'}</Label>
            <Textarea id="vin-respuesta" value={respuesta} maxLength={1000} onChange={(e) => setRespuesta(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDecision(null)} disabled={guardando}>Cancelar</Button>
            <Button onClick={() => void resolver()} disabled={guardando || (decision?.accion === 'rechazar' && !respuesta.trim())}
              variant={decision?.accion === 'rechazar' ? 'destructive' : 'default'}>
              {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              {decision?.accion === 'aprobar' ? 'Aprobar y vincular' : 'Rechazar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
