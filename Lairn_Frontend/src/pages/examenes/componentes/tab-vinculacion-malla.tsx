// Pestaña «Malla» del curso del docente (HU-01.10): muestra a qué asignatura oficial está
// vinculado el curso y permite pedir el vínculo al Administrador o al Coordinador.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { AlertTriangle, CheckCircle2, Link2, Loader2, Send, XCircle } from 'lucide-react'
import type { EstadoSolicitud, ProgramaVinculable, VinculacionCurso } from '@/types/vinculacion'

const ESTADO: Record<EstadoSolicitud, { texto: string; clase: string }> = {
  pendiente: { texto: 'Pendiente', clase: 'bg-warning/15 text-warning' },
  aprobada: { texto: 'Aprobada', clase: 'bg-success/15 text-success' },
  rechazada: { texto: 'Rechazada', clase: 'bg-destructive/15 text-destructive' },
  cancelada: { texto: 'Cancelada', clase: 'bg-muted text-muted-foreground' },
}
const fecha = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

function mensajeError(err: unknown, porDefecto: string) {
  const d = (err as { response?: { data?: Record<string, unknown> } }).response?.data
  if (!d) return porDefecto
  const v = d.detalle ?? Object.values(d)[0]
  return Array.isArray(v) ? String(v[0]) : String(v ?? porDefecto)
}

export function TabVinculacionMalla({ cursoId }: { cursoId: number }) {
  const [estado, setEstado] = useState<VinculacionCurso | null>(null)
  const [programas, setProgramas] = useState<ProgramaVinculable[]>([])
  const [programaId, setProgramaId] = useState('')
  const [asignaturaId, setAsignaturaId] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let vigente = true
    Promise.all([
      api.get<VinculacionCurso>(`/evaluacion/docente/cursos/${cursoId}/vinculacion/`),
      api.get<ProgramaVinculable[]>('/evaluacion/vinculacion/opciones/'),
    ])
      .then(([r1, r2]) => {
        if (!vigente) return
        setEstado(r1.data)
        setProgramas(r2.data)
      })
      .catch((err) => vigente && toast.error(mensajeError(err, 'No se pudo cargar el vínculo con la malla')))
    return () => {
      vigente = false
    }
  }, [cursoId, version])

  const programa = programas.find((p) => String(p.id) === programaId)
  const asignatura = programa?.asignaturas.find((a) => String(a.id) === asignaturaId)
  const itemsPrograma = programas.map((p) => ({ value: String(p.id), label: `${p.codigo} · ${p.nombre}` }))
  const itemsAsignatura = useMemo(
    () =>
      (programa?.asignaturas ?? []).map((a) => ({
        value: String(a.id),
        label: `${a.codigo} · ${a.nombre}${a.semestre ? ` (S${a.semestre})` : ''}${a.curso_vinculado ? ' · ya vinculada' : ''}`,
      })),
    [programa],
  )

  const enviar = async () => {
    if (!asignatura) return
    setEnviando(true)
    try {
      await api.post(`/evaluacion/docente/cursos/${cursoId}/vinculacion/`, { asignatura: asignatura.id, mensaje })
      toast.success('Solicitud enviada al Administrador y al Coordinador')
      setAsignaturaId('')
      setMensaje('')
      setVersion((v) => v + 1)
    } catch (err) {
      toast.error(mensajeError(err, 'No se pudo enviar la solicitud'))
    } finally {
      setEnviando(false)
    }
  }

  const cancelar = async (id: number) => {
    try {
      await api.post(`/evaluacion/vinculacion/solicitudes/${id}/cancelar/`)
      toast.success('Solicitud cancelada')
      setVersion((v) => v + 1)
    } catch (err) {
      toast.error(mensajeError(err, 'No se pudo cancelar'))
    }
  }

  if (!estado) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Link2 className="h-4 w-4 text-primary" aria-hidden />
            Vínculo con la malla curricular
          </CardTitle>
          <CardDescription>
            Para que tus evaluaciones, tareas y banco de preguntas cuenten en los resultados de aprendizaje, el curso debe
            estar vinculado a la asignatura oficial del programa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {estado.vinculadas.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-warning">
              <AlertTriangle className="h-4 w-4" aria-hidden />
              Este curso aún no está vinculado a ninguna asignatura de la malla.
            </p>
          ) : (
            <ul className="space-y-1.5">
              {estado.vinculadas.map((a) => (
                <li key={a.id} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden />
                  <span>
                    <b>{a.codigo} · {a.nombre}</b> — {a.programa.codigo} · {a.programa.nombre}
                    {a.semestre ? `, semestre ${a.semestre}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pedir vinculación</CardTitle>
          <CardDescription>El Administrador o el Coordinador del programa revisan y aprueban tu solicitud.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="min-w-0 space-y-1">
              <Label htmlFor="vin-programa">Programa</Label>
              <Select value={programaId} onValueChange={(v) => { setProgramaId(String(v ?? '')); setAsignaturaId('') }} items={itemsPrograma}>
                <SelectTrigger id="vin-programa" className="w-full min-w-0">
                  <SelectValue placeholder="Elige el programa" />
                </SelectTrigger>
                <SelectContent>
                  {itemsPrograma.map((i) => (
                    <SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="min-w-0 space-y-1">
              <Label htmlFor="vin-asignatura">Asignatura</Label>
              <Select value={asignaturaId} onValueChange={(v) => setAsignaturaId(String(v ?? ''))} items={itemsAsignatura} disabled={!programa}>
                <SelectTrigger id="vin-asignatura" className="w-full min-w-0">
                  <SelectValue placeholder={programa ? 'Elige la asignatura' : 'Primero elige el programa'} />
                </SelectTrigger>
                <SelectContent>
                  {itemsAsignatura.map((i) => (
                    <SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          {asignatura?.curso_vinculado && asignatura.curso_vinculado.id !== cursoId && (
            <p className="flex items-start gap-1.5 rounded-lg border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              Hoy la asignatura está vinculada al curso «{asignatura.curso_vinculado.nombre}» de {asignatura.curso_vinculado.docente}.
              Si aprueban tu solicitud, el vínculo pasa a tu curso.
            </p>
          )}
          <div className="space-y-1">
            <Label htmlFor="vin-mensaje">Mensaje para quien aprueba (opcional)</Label>
            <Textarea id="vin-mensaje" value={mensaje} maxLength={1000} onChange={(e) => setMensaje(e.target.value)}
              placeholder="Por ejemplo: soy el docente asignado a esta asignatura en el periodo 2026-2." />
          </div>
          <div className="flex justify-end">
            <Button onClick={() => void enviar()} disabled={!asignatura || enviando}>
              {enviando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Send className="mr-1.5 h-4 w-4" aria-hidden />}
              Enviar solicitud
            </Button>
          </div>
        </CardContent>
      </Card>

      {estado.solicitudes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mis solicitudes</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {estado.solicitudes.map((s) => (
                <li key={s.id} className="flex flex-wrap items-start justify-between gap-2 py-2.5 text-sm">
                  <div className="min-w-0 space-y-0.5">
                    <p className="font-medium">
                      {s.asignatura.codigo} · {s.asignatura.nombre}
                      <span className="font-normal text-muted-foreground"> — {s.asignatura.programa.codigo}</span>
                    </p>
                    <p className="text-xs text-muted-foreground">Enviada el {fecha.format(new Date(s.creada_en))}</p>
                    {s.respuesta && (
                      <p className="text-xs">
                        <b>Respuesta{s.resuelta_por ? ` de ${s.resuelta_por}` : ''}:</b> {s.respuesta}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={`border-transparent ${ESTADO[s.estado].clase}`}>{ESTADO[s.estado].texto}</Badge>
                    {s.estado === 'pendiente' && (
                      <Button variant="ghost" size="sm" onClick={() => void cancelar(s.id)}>
                        <XCircle className="mr-1 h-3.5 w-3.5" aria-hidden />
                        Cancelar
                      </Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
