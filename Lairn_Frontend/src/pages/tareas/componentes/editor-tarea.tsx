// Editor de una tarea en borrador (HU-08B.1 / 08B.2): datos, formatos,
// plazo y política de retraso, rúbrica y archivos guía. Una tarea publicada
// se muestra en solo lectura (los estudiantes ya pudieron entregar).

import { useRef, useState } from 'react'
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Download, FileUp, Loader2, Lock, Paperclip, Save, Send, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TareasDocente } from '../use-tareas-docente'
import { EditorRubrica } from './editor-rubrica'
import { FORMATOS, descargarArchivo, tamanoLegible } from '../utilidades-tareas'

export function EditorTarea({ td }: { td: TareasDocente }) {
  const inputGuia = useRef<HTMLInputElement>(null)
  const [confirmar, setConfirmar] = useState<'publicar' | 'eliminar' | null>(null)
  const publicada = td.abierta?.estado === 'publicada'
  const resultados = td.asignatura?.resultados ?? []
  const { form, setForm } = td

  return (
    <div className="min-w-0 space-y-4">
      {publicada && (
        <p className="flex items-center gap-2 rounded-lg bg-muted p-3 text-sm text-foreground">
          <Lock className="h-4 w-4" aria-hidden />
          Publicada: los estudiantes ya la ven, por eso no se puede editar.
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Datos de la tarea</CardTitle>
          <CardDescription>
            {td.abierta?.origen === 'ia' ? 'Generada con IA: revisa el texto antes de publicar.' : 'Qué deben hacer y entregar.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <fieldset disabled={publicada} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="tarea-ra">
                Resultado de aprendizaje que evidencia <span className="text-destructive" aria-hidden="true">*</span>
              </Label>
              <Select
                value={form.resultado}
                onValueChange={(v) => setForm({ ...form, resultado: v ?? '' })}
                items={resultados.map((r) => ({ value: String(r.id), label: r.descripcion }))}
                disabled={publicada}
              >
                <SelectTrigger id="tarea-ra" className="w-full">
                  <SelectValue placeholder="Elige el RA" />
                </SelectTrigger>
                <SelectContent>
                  {resultados.map((r) => (
                    <SelectItem key={r.id} value={String(r.id)}>
                      {r.descripcion}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tarea-titulo">
                Título <span className="text-destructive" aria-hidden="true">*</span>
              </Label>
              <Input id="tarea-titulo" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tarea-descripcion">
                Instrucciones y entregable <span className="text-destructive" aria-hidden="true">*</span>
              </Label>
              <Textarea
                id="tarea-descripcion"
                className="min-h-[160px]"
                value={form.descripcion}
                onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium" id="tarea-formatos">
                Formatos permitidos <span className="text-destructive" aria-hidden="true">*</span>
              </p>
              <div className="flex flex-wrap gap-2" role="group" aria-labelledby="tarea-formatos">
                {FORMATOS.map((f) => {
                  const activo = form.formatos_permitidos.includes(f.valor)
                  return (
                    <button
                      key={f.valor}
                      type="button"
                      aria-pressed={activo}
                      disabled={publicada}
                      onClick={() =>
                        setForm({
                          ...form,
                          formatos_permitidos: activo
                            ? form.formatos_permitidos.filter((x) => x !== f.valor)
                            : [...form.formatos_permitidos, f.valor],
                        })
                      }
                      className={cn(
                        'rounded-full border px-3 py-1 text-xs transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                        activo ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted',
                      )}
                    >
                      {f.etiqueta}
                    </button>
                  )
                })}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 sm:items-end">
              <div className="space-y-1.5">
                <Label htmlFor="tarea-limite">
                  Fecha límite <span className="text-destructive" aria-hidden="true">*</span>
                </Label>
                <Input
                  id="tarea-limite"
                  type="datetime-local"
                  value={form.fecha_limite}
                  onChange={(e) => setForm({ ...form, fecha_limite: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-2 pb-1.5">
                <Switch
                  id="tarea-tardias"
                  checked={form.permite_tardias}
                  onCheckedChange={(v) => setForm({ ...form, permite_tardias: v })}
                  disabled={publicada}
                />
                <Label htmlFor="tarea-tardias" className="font-normal">
                  Aceptar entregas tardías (se marcan "Con retraso")
                </Label>
              </div>
            </div>
          </fieldset>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Rúbrica de calificación</CardTitle>
          <CardDescription>Criterios, niveles de desempeño (0 a 5) y ponderaciones.</CardDescription>
        </CardHeader>
        <CardContent>
          <EditorRubrica rubrica={form.rubrica} alCambiar={(rubrica) => setForm({ ...form, rubrica })} deshabilitado={publicada} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Archivos guía</CardTitle>
          <CardDescription>Enunciados, plantillas o datos de apoyo (máx. 10 MB cada uno).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {td.abierta?.archivos_guia.length ? (
            <ul className="space-y-1.5">
              {td.abierta.archivos_guia.map((a) => (
                <li key={a.id} className="flex items-center gap-2 rounded-lg border border-border p-2 text-sm">
                  <Paperclip className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                  <span className="min-w-0 flex-1 truncate">{a.nombre}</span>
                  <span className="text-xs text-muted-foreground">{tamanoLegible(a.tamano)}</span>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`Descargar ${a.nombre}`}
                    onClick={() => void descargarArchivo(`/evaluacion/docente/tareas/${td.abierta?.id}/archivos/${a.id}/`, a.nombre)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  {!publicada && (
                    <Button variant="ghost" size="icon-sm" aria-label={`Quitar ${a.nombre}`} onClick={() => void td.quitarGuia(a.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Sin archivos guía.</p>
          )}
          {!publicada && (
            <>
              <input
                ref={inputGuia}
                type="file"
                className="sr-only"
                aria-label="Seleccionar archivo guía"
                accept=".pdf,.doc,.docx,.odt,.zip,.png,.jpg,.jpeg,.txt"
                onChange={(e) => {
                  const archivo = e.target.files?.[0]
                  if (archivo) void td.subirGuia(archivo)
                  e.target.value = ''
                }}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => inputGuia.current?.click()}
                disabled={td.subiendo || td.abiertaId === 'nueva'}
                title={td.abiertaId === 'nueva' ? 'Guarda el borrador para adjuntar archivos' : undefined}
              >
                {td.subiendo ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <FileUp className="mr-1.5 h-4 w-4" aria-hidden />}
                Adjuntar archivo
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {!publicada && (
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
          <div>
            {typeof td.abiertaId === 'number' && (
              <Button variant="ghost" onClick={() => setConfirmar('eliminar')}>
                <Trash2 className="mr-1.5 h-4 w-4 text-destructive" aria-hidden />
                Eliminar borrador
              </Button>
            )}
          </div>
          <div className="flex flex-col-reverse gap-2 sm:flex-row">
            <Button variant="outline" onClick={() => void td.guardar()} disabled={td.guardando || td.publicando}>
              {td.guardando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Save className="mr-1.5 h-4 w-4" aria-hidden />}
              Guardar borrador
            </Button>
            <Button
              onClick={() => setConfirmar('publicar')}
              disabled={typeof td.abiertaId !== 'number' || td.guardando}
              title={typeof td.abiertaId !== 'number' ? 'Guarda el borrador antes de publicar' : undefined}
            >
              <Send className="mr-1.5 h-4 w-4" aria-hidden />
              Publicar
            </Button>
          </div>
        </div>
      )}

      <Dialog open={confirmar !== null} onOpenChange={(v) => !v && setConfirmar(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{confirmar === 'publicar' ? 'Publicar tarea' : 'Eliminar borrador'}</DialogTitle>
            <DialogDescription>
              {confirmar === 'publicar'
                ? 'Se guardarán los cambios y los estudiantes del curso verán la tarea. Después no se podrá editar.'
                : 'El borrador y sus archivos guía se eliminarán. Esta acción no se deshace.'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmar(null)}>
              Cancelar
            </Button>
            <Button
              variant={confirmar === 'eliminar' ? 'destructive' : 'default'}
              disabled={td.publicando || td.guardando}
              onClick={async () => {
                if (confirmar === 'publicar') await td.publicar()
                else await td.eliminar()
                setConfirmar(null)
              }}
            >
              {(td.publicando || td.guardando) && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
              {confirmar === 'publicar' ? 'Publicar' : 'Eliminar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
