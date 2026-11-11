// Solicitudes de cuenta administrativa (HU-26): quien entra por el acceso de personal y elige
// Coordinador, Vicerrector o Administrador queda inactivo hasta que el Administrador lo apruebe aquí.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Check, Loader2, ShieldAlert, X } from 'lucide-react'
import { cn } from '@/lib/utils'

type Estado = 'pendiente' | 'aprobada' | 'rechazada'

interface SolicitudCuenta {
  id: number
  estado: Estado
  rol_solicitado: string
  motivo: string
  creada_en: string
  resuelta_en: string | null
  resuelta_por: string
  usuario: { id: number; nombre: string; email: string }
}

const FILTROS: { clave: Estado | 'todas'; texto: string }[] = [
  { clave: 'pendiente', texto: 'Pendientes' },
  { clave: 'aprobada', texto: 'Aprobadas' },
  { clave: 'rechazada', texto: 'Rechazadas' },
  { clave: 'todas', texto: 'Todas' },
]
const ETIQUETA: Record<Estado, string> = { pendiente: 'Pendiente', aprobada: 'Aprobada', rechazada: 'Rechazada' }
const fecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

export function TarjetaSolicitudesCuenta({ alAprobar }: { alAprobar: () => void }) {
  const [filtro, setFiltro] = useState<Estado | 'todas'>('pendiente')
  const [datos, setDatos] = useState<{ pendientes: number; solicitudes: SolicitudCuenta[] } | null>(null)
  const [version, setVersion] = useState(0)
  const [decision, setDecision] = useState<{ s: SolicitudCuenta; accion: 'aprobar' | 'rechazar' } | null>(null)
  const [motivo, setMotivo] = useState('')
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true
    api
      .get<{ pendientes: number; solicitudes: SolicitudCuenta[] }>(`/usuarios/administracion/solicitudes-cuenta/?estado=${filtro}`)
      .then((r) => vigente && setDatos(r.data))
      .catch(() => vigente && setDatos({ pendientes: 0, solicitudes: [] }))
    return () => {
      vigente = false
    }
  }, [filtro, version])

  const resolver = async () => {
    if (!decision) return
    setGuardando(true)
    try {
      await api.post(`/usuarios/administracion/solicitudes-cuenta/${decision.s.id}/${decision.accion}/`, { motivo })
      toast.success(decision.accion === 'aprobar' ? `Cuenta de ${decision.s.rol_solicitado} activada` : 'Solicitud rechazada')
      if (decision.accion === 'aprobar') alAprobar()
      setDecision(null)
      setMotivo('')
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
          <ShieldAlert className="h-4 w-4 text-primary" aria-hidden />
          Solicitudes de cuenta administrativa
          {!!datos?.pendientes && <Badge className="ml-1">{datos.pendientes}</Badge>}
        </CardTitle>
        <CardDescription>
          Coordinador, Vicerrector y Administrador entran con Google pero su cuenta queda inactiva hasta que la apruebes. Los
          docentes y estudiantes entran de inmediato.
        </CardDescription>
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
        {datos === null ? (
          <div className="flex justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-primary" aria-label="Cargando" />
          </div>
        ) : datos.solicitudes.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">No hay solicitudes en este estado.</p>
        ) : (
          <ul className="divide-y divide-border rounded-xl border border-border">
            {datos.solicitudes.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm">
                <div className="min-w-0">
                  <p className="font-medium">{s.usuario.nombre}</p>
                  <p className="truncate text-xs text-muted-foreground">{s.usuario.email}</p>
                  <p className="text-xs text-muted-foreground">
                    Pide el rol <b className="text-foreground">{s.rol_solicitado}</b> · {fecha.format(new Date(s.creada_en))}
                  </p>
                  {s.estado !== 'pendiente' && (
                    <p className="text-xs text-muted-foreground">
                      {ETIQUETA[s.estado]}{s.resuelta_por ? ` por ${s.resuelta_por}` : ''}{s.motivo ? `: ${s.motivo}` : ''}
                    </p>
                  )}
                </div>
                {s.estado === 'pendiente' ? (
                  <div className="flex gap-1.5">
                    <Button size="sm" onClick={() => setDecision({ s, accion: 'aprobar' })}>
                      <Check className="mr-1 h-3.5 w-3.5" aria-hidden />
                      Aprobar
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setDecision({ s, accion: 'rechazar' })}>
                      <X className="mr-1 h-3.5 w-3.5" aria-hidden />
                      Rechazar
                    </Button>
                  </div>
                ) : (
                  <Badge variant="outline">{ETIQUETA[s.estado]}</Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      <Dialog open={!!decision} onOpenChange={(v) => !v && setDecision(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{decision?.accion === 'aprobar' ? 'Aprobar cuenta' : 'Rechazar solicitud'}</DialogTitle>
            <DialogDescription>
              {decision && `${decision.s.usuario.nombre} (${decision.s.usuario.email}) como ${decision.s.rol_solicitado}`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1">
            <Label htmlFor="sc-motivo">{decision?.accion === 'rechazar' ? 'Motivo del rechazo *' : 'Nota (opcional)'}</Label>
            <Textarea id="sc-motivo" value={motivo} maxLength={1000} onChange={(e) => setMotivo(e.target.value)}
              placeholder={decision?.accion === 'rechazar' ? 'La persona lo verá al intentar entrar.' : ''} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDecision(null)} disabled={guardando}>Cancelar</Button>
            <Button onClick={() => void resolver()} disabled={guardando || (decision?.accion === 'rechazar' && !motivo.trim())}
              variant={decision?.accion === 'rechazar' ? 'destructive' : 'default'}>
              {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              {decision?.accion === 'aprobar' ? 'Aprobar y activar' : 'Rechazar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
