// Diálogos de curaduría: editar una pregunta pendiente (HU-05.2) y
// confirmar su descarte con un motivo opcional (HU-05.4).
// El formulario se reinicia con cada pregunta porque el componente se
// monta con `key={pregunta.id}`.

import { useState } from 'react'
import { Button } from '@/components/ui/button'
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
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Plus, Trash2 } from 'lucide-react'
import type { EdicionPregunta, PreguntaBanco } from '@/types/banco'
import type { BancoPreguntas } from '../use-banco-preguntas'

const MIN_OPCIONES = 2
const MAX_OPCIONES = 6

function FormularioEdicion({ pregunta, bp }: { pregunta: PreguntaBanco; bp: BancoPreguntas }) {
  const [form, setForm] = useState<EdicionPregunta>({
    contexto: pregunta.contexto,
    enunciado: pregunta.enunciado,
    opciones: [...pregunta.opciones],
    respuesta_correcta: pregunta.respuesta_correcta,
    retroalimentacion: pregunta.retroalimentacion,
  })
  const guardando = bp.procesandoId === pregunta.id

  // Errores visibles antes de enviar; el backend vuelve a validar igual.
  const opcionesLimpias = form.opciones.map((o) => o.trim().toLowerCase())
  const error = !form.enunciado.trim()
    ? 'El enunciado es obligatorio.'
    : opcionesLimpias.some((o) => !o)
      ? 'Ninguna opción puede quedar vacía.'
      : new Set(opcionesLimpias).size !== opcionesLimpias.length
        ? 'Hay opciones repetidas.'
        : ''

  const cambiarOpcion = (i: number, texto: string) =>
    setForm({ ...form, opciones: form.opciones.map((o, j) => (j === i ? texto : o)) })

  const quitarOpcion = (i: number) => {
    const opciones = form.opciones.filter((_, j) => j !== i)
    // Si se quita la correcta o una anterior, el índice se ajusta.
    let correcta = form.respuesta_correcta
    if (i === correcta) correcta = 0
    else if (i < correcta) correcta -= 1
    setForm({ ...form, opciones, respuesta_correcta: correcta })
  }

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="edicion-contexto">Caso o situación</Label>
          <Textarea
            id="edicion-contexto"
            value={form.contexto}
            onChange={(e) => setForm({ ...form, contexto: e.target.value })}
            className="min-h-[90px]"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="edicion-enunciado">
            Enunciado <span className="text-destructive" aria-hidden="true">*</span>
          </Label>
          <Textarea
            id="edicion-enunciado"
            value={form.enunciado}
            onChange={(e) => setForm({ ...form, enunciado: e.target.value })}
          />
        </div>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Opciones (marca la correcta)</legend>
          {form.opciones.map((opcion, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="radio"
                name="opcion-correcta"
                checked={form.respuesta_correcta === i}
                onChange={() => setForm({ ...form, respuesta_correcta: i })}
                aria-label={`Marcar la opción ${i + 1} como correcta`}
                className="h-4 w-4 shrink-0 accent-primary"
              />
              <Input
                value={opcion}
                onChange={(e) => cambiarOpcion(i, e.target.value)}
                aria-label={`Texto de la opción ${i + 1}`}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                onClick={() => quitarOpcion(i)}
                disabled={form.opciones.length <= MIN_OPCIONES}
                aria-label={`Quitar la opción ${i + 1}`}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
          {form.opciones.length < MAX_OPCIONES && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setForm({ ...form, opciones: [...form.opciones, ''] })}
            >
              <Plus className="mr-1.5 h-4 w-4" aria-hidden />
              Agregar opción
            </Button>
          )}
        </fieldset>
        <div className="space-y-1.5">
          <Label htmlFor="edicion-retro">Justificación de la respuesta</Label>
          <Textarea
            id="edicion-retro"
            value={form.retroalimentacion}
            onChange={(e) => setForm({ ...form, retroalimentacion: e.target.value })}
          />
        </div>
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => bp.setEditando(null)} disabled={guardando}>
          Cancelar
        </Button>
        <Button onClick={() => bp.guardarEdicion(pregunta.id, form)} disabled={guardando || !!error}>
          {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
          Guardar cambios
        </Button>
      </DialogFooter>
    </>
  )
}

function FormularioDescarte({ pregunta, bp }: { pregunta: PreguntaBanco; bp: BancoPreguntas }) {
  const [motivo, setMotivo] = useState('')
  const procesando = bp.procesandoId === pregunta.id
  return (
    <>
      <div className="space-y-1.5">
        <Label htmlFor="motivo-descarte">Motivo (opcional)</Label>
        <Textarea
          id="motivo-descarte"
          placeholder="Ej.: opciones ambiguas, no evalúa el resultado de aprendizaje…"
          value={motivo}
          maxLength={300}
          onChange={(e) => setMotivo(e.target.value)}
        />
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => bp.setDescartando(null)} disabled={procesando}>
          Cancelar
        </Button>
        <Button variant="destructive" onClick={() => bp.descartar(pregunta.id, motivo)} disabled={procesando}>
          {procesando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
          Descartar pregunta
        </Button>
      </DialogFooter>
    </>
  )
}

export function DialogosPregunta({ bp }: { bp: BancoPreguntas }) {
  return (
    <>
      <Dialog open={!!bp.editando} onOpenChange={(abierto) => !abierto && bp.setEditando(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Editar pregunta</DialogTitle>
            <DialogDescription>
              Ajusta el contenido antes de aprobarla. Sigue pendiente hasta que la apruebes.
            </DialogDescription>
          </DialogHeader>
          {bp.editando && <FormularioEdicion key={bp.editando.id} pregunta={bp.editando} bp={bp} />}
        </DialogContent>
      </Dialog>

      <Dialog open={!!bp.descartando} onOpenChange={(abierto) => !abierto && bp.setDescartando(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Descartar pregunta</DialogTitle>
            <DialogDescription>
              No entrará al banco oficial ni podrá usarse en evaluaciones. Esta acción no se deshace.
            </DialogDescription>
          </DialogHeader>
          {bp.descartando && <FormularioDescarte key={bp.descartando.id} pregunta={bp.descartando} bp={bp} />}
        </DialogContent>
      </Dialog>
    </>
  )
}
