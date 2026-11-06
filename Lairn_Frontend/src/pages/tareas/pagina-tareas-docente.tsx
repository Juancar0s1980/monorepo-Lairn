// Tareas prácticas del docente (HU-08B).
//
// - Crear a mano o generar con IA desde un resultado de aprendizaje (la
//   rúbrica parte de la del RA cuando existe).
// - Editar el borrador (instrucciones, formatos, plazo, política de retraso,
//   rúbrica, archivos guía) y publicarlo para los estudiantes del curso.
// - En una tarea publicada: panel de entregas y calificación por rúbrica.
// La tarea es independiente del momento de evaluación; la coordinación puede
// usarla como evaluación formal de tipo "tarea" (HU-06.4).

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
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
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { BookOpenCheck, Loader2, Plus, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FormatoEntrega } from '@/types/tarea'
import { useTareasDocente } from './use-tareas-docente'
import { EditorTarea } from './componentes/editor-tarea'
import { PanelEntregas } from './componentes/panel-entregas'
import { FORMATOS, formatoFecha } from './utilidades-tareas'

export default function PaginaTareasDocente() {
  const td = useTareasDocente()
  const [dialogoIA, setDialogoIA] = useState(false)
  const [ia, setIa] = useState<{ resultado: string; fecha_limite: string; formatos_permitidos: FormatoEntrega[] }>({
    resultado: '',
    fecha_limite: '',
    formatos_permitidos: ['pdf'],
  })

  if (td.cargando) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  const encabezado = (
    <EncabezadoPagina
      eyebrow="Panel del docente"
      titulo="Tareas"
      subtitulo="Crea tareas con fecha límite y rúbrica, recibe las entregas de tus estudiantes y califícalas."
    />
  )

  if (td.errorCarga || !td.asignaturas.length) {
    return (
      <div className="space-y-6">
        {encabezado}
        <Card>
          <CardContent className="space-y-2 p-6 text-sm">
            <BookOpenCheck className="h-8 w-8 text-primary" aria-hidden />
            <p className="font-medium text-foreground">{td.errorCarga || 'Aún no tienes asignaturas asignadas'}</p>
            {!td.errorCarga && (
              <p className="text-muted-foreground">
                La coordinación académica debe vincular tu curso a una asignatura de la malla para que puedas crear tareas.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  const resultados = td.asignatura?.resultados ?? []

  return (
    <div className="space-y-6">
      {encabezado}

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <Select
          value={td.asignaturaId}
          onValueChange={(v) => v && td.elegirAsignatura(v)}
          items={td.asignaturas.map((a) => ({ value: String(a.id), label: `${a.codigo} — ${a.nombre}` }))}
        >
          <SelectTrigger className="w-full md:w-[360px]" aria-label="Asignatura">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {td.asignaturas.map((a) => (
              <SelectItem key={a.id} value={String(a.id)}>
                {a.codigo} — {a.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button
            variant="outline"
            onClick={() => {
              setIa({ resultado: resultados[0] ? String(resultados[0].id) : '', fecha_limite: '', formatos_permitidos: ['pdf'] })
              setDialogoIA(true)
            }}
            disabled={!resultados.length}
          >
            <Sparkles className="mr-1.5 h-4 w-4" aria-hidden />
            Generar con IA
          </Button>
          <Button onClick={td.nueva} disabled={!resultados.length}>
            <Plus className="mr-1.5 h-4 w-4" aria-hidden />
            Nueva tarea
          </Button>
        </div>
      </div>
      {!resultados.length && (
        <p className="text-sm text-muted-foreground">
          Esta asignatura no tiene resultados de aprendizaje; la coordinación debe registrarlos antes de crear tareas.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <section aria-label="Tareas de la asignatura" className="space-y-2">
          {td.tareas.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aún no hay tareas en esta asignatura.</p>
          ) : (
            td.tareas.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => td.abrir(t)}
                aria-current={td.abiertaId === t.id ? 'true' : undefined}
                className={cn(
                  'w-full rounded-xl border p-3 text-left transition-colors hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                  td.abiertaId === t.id ? 'border-primary bg-primary/5' : 'border-border',
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-foreground">{t.titulo}</span>
                  <Badge
                    className={cn(
                      'shrink-0 border-transparent',
                      t.estado === 'publicada' ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground',
                    )}
                  >
                    {t.estado === 'publicada' ? 'Publicada' : 'Borrador'}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">Entrega: {formatoFecha.format(new Date(t.fecha_limite))}</p>
                <p className="text-xs text-muted-foreground">
                  {t.total_entregas} entrega{t.total_entregas === 1 ? '' : 's'}
                  {t.origen === 'ia' && ' · generada con IA'}
                </p>
              </button>
            ))
          )}
        </section>

        {td.abiertaId === null ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Elige una tarea de la lista, crea una nueva o genérala con IA a partir de un resultado de aprendizaje.
            </CardContent>
          </Card>
        ) : (
          <div className="min-w-0 space-y-4">
            <EditorTarea td={td} />
            {td.abierta?.estado === 'publicada' && <PanelEntregas td={td} tarea={td.abierta} />}
          </div>
        )}
      </div>

      <Dialog open={dialogoIA} onOpenChange={setDialogoIA}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Generar tarea con IA</DialogTitle>
            <DialogDescription>
              La IA redacta el escenario, las instrucciones y el entregable a partir del resultado de aprendizaje. Queda
              como borrador para que lo revises.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="ia-ra">Resultado de aprendizaje</Label>
              <Select
                value={ia.resultado}
                onValueChange={(v) => setIa({ ...ia, resultado: v ?? '' })}
                items={resultados.map((r) => ({ value: String(r.id), label: r.descripcion }))}
              >
                <SelectTrigger id="ia-ra" className="w-full">
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
              <Label htmlFor="ia-limite">Fecha límite de entrega</Label>
              <Input
                id="ia-limite"
                type="datetime-local"
                value={ia.fecha_limite}
                onChange={(e) => setIa({ ...ia, fecha_limite: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium" id="ia-formatos">Formatos permitidos</p>
              <div className="flex flex-wrap gap-2" role="group" aria-labelledby="ia-formatos">
                {FORMATOS.map((f) => {
                  const activo = ia.formatos_permitidos.includes(f.valor)
                  return (
                    <button
                      key={f.valor}
                      type="button"
                      aria-pressed={activo}
                      onClick={() =>
                        setIa({
                          ...ia,
                          formatos_permitidos: activo
                            ? ia.formatos_permitidos.filter((x) => x !== f.valor)
                            : [...ia.formatos_permitidos, f.valor],
                        })
                      }
                      className={cn(
                        'rounded-full border px-3 py-1 text-xs',
                        activo ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground',
                      )}
                    >
                      {f.etiqueta}
                    </button>
                  )
                })}
              </div>
            </div>
            {td.generando && (
              <p role="status" className="text-xs text-muted-foreground">
                La IA está redactando la tarea; puede tardar hasta un minuto.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogoIA(false)} disabled={td.generando}>
              Cancelar
            </Button>
            <Button
              disabled={!ia.resultado || !ia.fecha_limite || !ia.formatos_permitidos.length || td.generando}
              onClick={async () => {
                if (await td.generar(ia)) setDialogoIA(false)
              }}
            >
              {td.generando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Sparkles className="mr-1.5 h-4 w-4" aria-hidden />}
              Generar borrador
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
