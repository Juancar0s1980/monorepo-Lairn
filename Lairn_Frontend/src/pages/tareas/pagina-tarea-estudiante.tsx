// Detalle de una tarea para el estudiante (HU-08A.1 a 08A.4).
//
// - Instrucciones, archivos guía, fecha límite con tiempo restante y rúbrica.
// - Envío DEFINITIVO de un único archivo: no hay borrador; se confirma antes.
//   Si el plazo venció y el docente no acepta tardías, el envío se deshabilita.
// - Tras calificar: nota, nivel por criterio y observaciones del docente.

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, ArrowLeft, CheckCircle2, Clock, Download, FileUp, Loader2, Paperclip, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TareaEstudiante } from '@/types/tarea'
import { mensajeError } from '@/pages/academico/academico-utils'
import { ETIQUETA_ENTREGA, descargarArchivo, formatoFecha, tamanoLegible, tiempoRestante } from './utilidades-tareas'

const TAMANO_MAXIMO = 20 * 1024 * 1024

export default function PaginaTareaEstudiante() {
  const { tareaId = '' } = useParams()
  const [tarea, setTarea] = useState<TareaEstudiante | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [errorArchivo, setErrorArchivo] = useState('')
  const [confirmar, setConfirmar] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const res = await api.get<TareaEstudiante>(`/evaluacion/estudiante/tareas/${tareaId}/`)
        if (activo) setTarea(res.data)
      } catch (err: unknown) {
        if (activo) setError(mensajeError(err, 'No se encontró la tarea.'))
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => {
      activo = false
    }
  }, [tareaId])

  const volver = (
    <Link to="/mis-tareas" className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Volver a mis tareas
    </Link>
  )

  if (cargando) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }
  if (error || !tarea) {
    return (
      <div className="space-y-4">
        {volver}
        <p role="alert" className="text-sm text-destructive">{error || 'No se encontró la tarea.'}</p>
      </div>
    )
  }

  const elegir = (f: File | null) => {
    setErrorArchivo('')
    setArchivo(null)
    if (!f) return
    const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
    if (!tarea.extensiones.includes(ext)) {
      setErrorArchivo(`Formato no permitido. Usa: ${tarea.extensiones.join(', ')}.`)
      return
    }
    if (f.size > TAMANO_MAXIMO) {
      setErrorArchivo('El archivo supera los 20 MB.')
      return
    }
    setArchivo(f)
  }

  const enviar = async () => {
    if (!archivo || enviando) return
    setEnviando(true)
    try {
      const datos = new FormData()
      datos.append('archivo', archivo)
      const res = await api.post<TareaEstudiante>(`/evaluacion/estudiante/tareas/${tarea.id}/entregar/`, datos, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      setTarea(res.data)
      setArchivo(null)
      toast.success('Entrega enviada')
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo enviar la entrega'))
    } finally {
      setEnviando(false)
      setConfirmar(false)
    }
  }

  const entrega = tarea.mi_entrega
  const calificacion = entrega?.calificacion

  return (
    <div className="space-y-6">
      {volver}
      <div className="space-y-1">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-primary uppercase">
          {tarea.asignatura.codigo} — {tarea.asignatura.nombre}
        </p>
        <h1 className="font-heading text-3xl text-foreground">{tarea.titulo}</h1>
        <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" aria-hidden />
          Fecha límite: {formatoFecha.format(new Date(tarea.fecha_limite))}
          {!entrega && (
            <Badge
              className={cn(
                'border-transparent',
                tarea.estado_plazo === 'abierta' ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive',
              )}
            >
              {tarea.estado_plazo === 'cerrada' ? 'Cerrada' : tiempoRestante(tarea.fecha_limite)}
            </Badge>
          )}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="min-w-0 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Instrucciones</CardTitle>
              <CardDescription>Resultado de aprendizaje: {tarea.resultado_descripcion}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm whitespace-pre-line text-foreground">{tarea.descripcion}</p>
              {tarea.archivos_guia.length > 0 && (
                <ul className="space-y-1.5" aria-label="Archivos guía">
                  {tarea.archivos_guia.map((a) => (
                    <li key={a.id} className="flex items-center gap-2 rounded-lg border border-border p-2 text-sm">
                      <Paperclip className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                      <span className="min-w-0 flex-1 truncate">{a.nombre}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => void descargarArchivo(`/evaluacion/estudiante/tareas/${tarea.id}/archivos/${a.id}/`, a.nombre)}
                      >
                        <Download className="mr-1 h-4 w-4" aria-hidden />
                        Descargar
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Rúbrica</CardTitle>
              <CardDescription>Así se calificará tu entrega (escala 0 a 5).</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Criterio</TableHead>
                    <TableHead className="text-right">Peso</TableHead>
                    <TableHead>Niveles</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tarea.rubrica.map((c, i) => {
                    const elegido = calificacion?.niveles_elegidos[i]
                    return (
                      <TableRow key={i}>
                        <TableCell className="font-medium whitespace-normal">{c.criterio}</TableCell>
                        <TableCell className="text-right">{c.peso} %</TableCell>
                        <TableCell className="whitespace-normal">
                          <div className="flex flex-wrap gap-1">
                            {c.niveles.map((n, k) => (
                              <Badge
                                key={k}
                                variant="outline"
                                className={cn(elegido === k && 'border-primary bg-primary/10 text-primary')}
                              >
                                {n.nombre} · {n.valor}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div className="min-w-0 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tu entrega</CardTitle>
              <CardDescription>Formatos: {tarea.extensiones.join(', ')} · máx. 20 MB</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {entrega ? (
                <>
                  <p role="status" className="flex items-start gap-2 text-sm text-foreground">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden />
                    Enviada el {formatoFecha.format(new Date(entrega.enviada_en))}
                  </p>
                  <Badge className={cn('border-transparent', ETIQUETA_ENTREGA[entrega.estado].clase)}>
                    {ETIQUETA_ENTREGA[entrega.estado].texto}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => void descargarArchivo(`/evaluacion/estudiante/entregas/${entrega.id}/archivo/`, entrega.nombre)}
                  >
                    <Download className="mr-1.5 h-4 w-4" aria-hidden />
                    {entrega.nombre} ({tamanoLegible(entrega.tamano)})
                  </Button>
                </>
              ) : tarea.estado_plazo === 'cerrada' ? (
                <p role="alert" className="flex items-start gap-2 text-sm text-destructive">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                  El plazo terminó y esta tarea no acepta entregas tardías.
                </p>
              ) : (
                <>
                  {tarea.estado_plazo === 'tardia' && (
                    <p className="text-sm text-foreground">El plazo venció: tu entrega quedará marcada "Con retraso".</p>
                  )}
                  <input
                    ref={input}
                    type="file"
                    className="sr-only"
                    aria-label="Seleccionar archivo de entrega"
                    accept={tarea.extensiones.map((e) => `.${e}`).join(',')}
                    onChange={(e) => elegir(e.target.files?.[0] ?? null)}
                  />
                  <Button variant="outline" className="w-full" onClick={() => input.current?.click()} disabled={enviando}>
                    <FileUp className="mr-1.5 h-4 w-4" aria-hidden />
                    {archivo ? 'Cambiar archivo' : 'Seleccionar archivo'}
                  </Button>
                  {archivo && (
                    <p className="text-xs break-all text-muted-foreground">
                      {archivo.name} ({tamanoLegible(archivo.size)})
                    </p>
                  )}
                  {errorArchivo && (
                    <p role="alert" className="text-sm text-destructive">{errorArchivo}</p>
                  )}
                  <Button className="w-full" disabled={!archivo || enviando} onClick={() => setConfirmar(true)}>
                    <Send className="mr-1.5 h-4 w-4" aria-hidden />
                    Enviar entrega
                  </Button>
                  <p className="text-xs text-muted-foreground">El envío es definitivo: no se puede reemplazar el archivo.</p>
                </>
              )}
            </CardContent>
          </Card>

          {calificacion && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Calificación</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-3xl font-bold text-primary">
                  {calificacion.nota}
                  <span className="text-base font-normal text-muted-foreground"> / 5.00</span>
                </p>
                {calificacion.observaciones && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Observaciones del docente</p>
                    <p className="text-sm whitespace-pre-line text-foreground">{calificacion.observaciones}</p>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">El nivel obtenido en cada criterio está resaltado en la rúbrica.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={confirmar} onOpenChange={setConfirmar}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>¿Enviar tu entrega?</DialogTitle>
            <DialogDescription>
              Se enviará "{archivo?.name}". Es un envío definitivo: después no podrás cambiar el archivo.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmar(false)} disabled={enviando}>
              Revisar de nuevo
            </Button>
            <Button onClick={() => void enviar()} disabled={enviando}>
              {enviando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              Enviar definitivamente
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
