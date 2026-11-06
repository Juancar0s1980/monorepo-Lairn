// Pestaña "Alertas" (HU-10): tablero de alerta temprana del programa.
//
// - Administrador: define la regla (HU-10.1) y exporta el listado a CSV (HU-10.3).
// - Coordinador y Administrador: ven las alertas de estudiantes y cursos por
//   debajo del umbral (HU-10.2) y registran la acción de seguimiento.
// Las alertas se recalculan en el servidor cada vez que se abre el tablero.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { BellRing, Download, Loader2, Save, UserRound, Users } from 'lucide-react'
import type { Academico } from '../use-academico'
import { mensajeError } from '../academico-utils'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'

interface Regla {
  porcentaje_minimo: number
  actividades_minimas: number
  activa: boolean
}

interface Alerta {
  id: number
  tipo: 'estudiante' | 'curso'
  estado: 'abierta' | 'atendida' | 'resuelta'
  estudiante: { id: number; nombre: string; email: string } | null
  asignatura: { id: number; codigo: string; nombre: string } | null
  actividades_bajas: number
  total_actividades: number
  detalle: { tipo: 'evaluacion' | 'tarea'; nombre: string; asignatura: string; porcentaje: number }[]
  nota_seguimiento: string
  atendida_en: string | null
  creada_en: string
}

const ESTADOS = [
  { valor: 'abierta', etiqueta: 'Abiertas' },
  { valor: 'atendida', etiqueta: 'Atendidas' },
  { valor: 'resuelta', etiqueta: 'Resueltas' },
] as const

const formatoFecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' })

export function TabAlertas({ ac, alCambiarAbiertas }: { ac: Academico; alCambiarAbiertas: (n: number) => void }) {
  const [estado, setEstado] = useState<(typeof ESTADOS)[number]['valor']>('abierta')
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [regla, setRegla] = useState<Regla>({ porcentaje_minimo: 60, actividades_minimas: 3, activa: true })
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  const clave = `${ac.programaId}|${estado}|${version}`
  const [claveCargada, setClaveCargada] = useState('')
  const cargando = !!ac.programaId && claveCargada !== clave
  const [guardandoRegla, setGuardandoRegla] = useState(false)
  const [atendiendo, setAtendiendo] = useState<Alerta | null>(null)
  const [nota, setNota] = useState('')
  const [enviandoNota, setEnviandoNota] = useState(false)

  useEffect(() => {
    if (!ac.programaId) return
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<{ regla: Regla; abiertas: number; alertas: Alerta[] }>(
          `/evaluacion/programas/${ac.programaId}/alertas/?estado=${estado}`,
        )
        if (!activo) return
        setAlertas(res.data.alertas)
        setRegla(res.data.regla)
        alCambiarAbiertas(res.data.abiertas)
        setError('')
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se pudieron cargar las alertas.'))
      } finally {
        if (activo) setClaveCargada(`${ac.programaId}|${estado}|${version}`)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [ac.programaId, estado, version, alCambiarAbiertas])

  const guardarRegla = async () => {
    setGuardandoRegla(true)
    try {
      const res = await api.put<Regla & { resumen: { creadas: number; resueltas: number } }>('/evaluacion/alertas/regla/', regla)
      toast.success(`Regla guardada · ${res.data.resumen.creadas} alerta(s) nueva(s), ${res.data.resumen.resueltas} resuelta(s)`)
      setVersion((n) => n + 1)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la regla'))
    } finally {
      setGuardandoRegla(false)
    }
  }

  const atender = async () => {
    if (!atendiendo) return
    setEnviandoNota(true)
    try {
      await api.post(`/evaluacion/alertas/${atendiendo.id}/atender/`, { nota })
      toast.success('Seguimiento registrado')
      setAtendiendo(null)
      setVersion((n) => n + 1)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo registrar el seguimiento'))
    } finally {
      setEnviandoNota(false)
    }
  }

  const exportar = async () => {
    try {
      const programa = ac.programas.find((p) => String(p.id) === ac.programaId)
      await descargarArchivo(
        `/evaluacion/programas/${ac.programaId}/alertas/exportar/?estado=${estado}`,
        `alertas_${programa?.codigo ?? 'programa'}.csv`,
      )
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo exportar el listado'))
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BellRing className="h-4 w-4 text-primary" aria-hidden />
            Regla de alerta temprana
          </CardTitle>
          <CardDescription>
            {regla.activa
              ? `Se alerta cuando un estudiante o curso tiene ${regla.actividades_minimas} o más actividades por debajo del ${regla.porcentaje_minimo} %.`
              : 'Las alertas están desactivadas.'}{' '}
            Actividad = evaluación formal presentada (% de aciertos) o tarea calificada (nota ÷ 5).
          </CardDescription>
        </CardHeader>
        {ac.esAdmin && (
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
              <div className="space-y-1.5">
                <Label htmlFor="regla-porcentaje">Desempeño mínimo (%)</Label>
                <Input
                  id="regla-porcentaje"
                  type="number"
                  min={1}
                  max={100}
                  value={regla.porcentaje_minimo}
                  onChange={(e) => setRegla({ ...regla, porcentaje_minimo: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="regla-actividades">Actividades por debajo para alertar</Label>
                <Input
                  id="regla-actividades"
                  type="number"
                  min={1}
                  max={50}
                  value={regla.actividades_minimas}
                  onChange={(e) => setRegla({ ...regla, actividades_minimas: Number(e.target.value) })}
                />
              </div>
              <div className="flex items-center gap-2 pb-1.5">
                <Switch id="regla-activa" checked={regla.activa} onCheckedChange={(v) => setRegla({ ...regla, activa: v })} />
                <Label htmlFor="regla-activa" className="font-normal">Activa</Label>
              </div>
              <Button onClick={() => void guardarRegla()} disabled={guardandoRegla}>
                {guardandoRegla ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Save className="mr-1.5 h-4 w-4" aria-hidden />}
                Guardar regla
              </Button>
            </div>
          </CardContent>
        )}
      </Card>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Tabs value={estado} onValueChange={(v) => setEstado(v as typeof estado)}>
          <TabsList className="bg-muted">
            {ESTADOS.map((e) => (
              <TabsTrigger key={e.valor} value={e.valor}>{e.etiqueta}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        {ac.esAdmin && (
          <Button variant="outline" onClick={() => void exportar()} disabled={!alertas.length}>
            <Download className="mr-1.5 h-4 w-4" aria-hidden />
            Exportar listado (Excel)
          </Button>
        )}
      </div>

      {cargando ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando alertas" />
        </div>
      ) : error ? (
        <p role="alert" className="text-sm text-destructive">{error}</p>
      ) : alertas.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            {estado === 'abierta' ? 'No hay estudiantes ni cursos en alerta con la regla actual.' : 'No hay alertas en este estado.'}
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-3">
          {alertas.map((a) => (
            <li key={a.id}>
              <Card>
                <CardContent className="space-y-3 p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-start gap-2">
                      {a.tipo === 'estudiante' ? (
                        <UserRound className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                      ) : (
                        <Users className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                      )}
                      <div>
                        <p className="font-medium text-foreground">
                          {a.tipo === 'estudiante' ? a.estudiante?.nombre : `${a.asignatura?.codigo} — ${a.asignatura?.nombre}`}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {a.tipo === 'estudiante' ? a.estudiante?.email : 'Curso'} · detectada el {formatoFecha.format(new Date(a.creada_en))}
                        </p>
                      </div>
                    </div>
                    <Badge className="w-fit border-transparent bg-destructive/10 text-destructive">
                      {a.actividades_bajas} de {a.total_actividades} actividades bajo el umbral
                    </Badge>
                  </div>
                  <ul className="flex flex-wrap gap-1.5" aria-label="Actividades por debajo del umbral">
                    {a.detalle.map((d, i) => (
                      <li key={i}>
                        <Badge variant="outline" className="max-w-full whitespace-normal">
                          {d.tipo === 'tarea' ? 'Tarea' : 'Evaluación'}: {d.nombre} · {d.porcentaje}%
                        </Badge>
                      </li>
                    ))}
                  </ul>
                  {a.estado === 'atendida' && (
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">Seguimiento:</span> {a.nota_seguimiento}
                    </p>
                  )}
                  {a.estado === 'abierta' && (
                    <div className="flex justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setNota('')
                          setAtendiendo(a)
                        }}
                      >
                        Registrar seguimiento
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={!!atendiendo} onOpenChange={(v) => !v && setAtendiendo(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar seguimiento</DialogTitle>
            <DialogDescription>
              {atendiendo?.tipo === 'estudiante' ? atendiendo?.estudiante?.nombre : atendiendo?.asignatura?.nombre}: describe la
              acción preventiva (tutoría, reunión, plan de mejora…). La alerta pasará a "Atendida".
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="nota-seguimiento">
              Acción realizada <span className="text-destructive" aria-hidden="true">*</span>
            </Label>
            <Textarea id="nota-seguimiento" value={nota} onChange={(e) => setNota(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAtendiendo(null)} disabled={enviandoNota}>
              Cancelar
            </Button>
            <Button onClick={() => void atender()} disabled={!nota.trim() || enviandoNota}>
              {enviandoNota && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
