// Edición de una guía del centro de ayuda (solo Administrador, ADR-018).

import { useState } from 'react'
import api from '@/services/api'
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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { ArrowDown, ArrowUp, Loader2, Plus, Trash2 } from 'lucide-react'
import type { ArticuloAyuda, PasoAyuda } from '@/types/ayuda'
import { mensajeError } from '@/pages/academico/academico-utils'

export function EditorGuia({
  abierto,
  guia,
  alCerrar,
  alGuardar,
}: {
  abierto: boolean
  guia: ArticuloAyuda
  alCerrar: () => void
  alGuardar: (g: ArticuloAyuda) => void
}) {
  return (
    <Dialog open={abierto} onOpenChange={(v) => !v && alCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        {/* El formulario se monta al abrir, con los valores actuales de la guía. */}
        {abierto && <Formulario guia={guia} alCerrar={alCerrar} alGuardar={alGuardar} />}
      </DialogContent>
    </Dialog>
  )
}

function Formulario({ guia, alCerrar, alGuardar }: { guia: ArticuloAyuda; alCerrar: () => void; alGuardar: (g: ArticuloAyuda) => void }) {
  const [titulo, setTitulo] = useState(guia.titulo)
  const [resumen, setResumen] = useState(guia.resumen)
  const [notas, setNotas] = useState(guia.notas ?? '')
  const [pasos, setPasos] = useState<PasoAyuda[]>(guia.pasos ?? [])
  const [publicado, setPublicado] = useState(guia.publicado)
  const [guardando, setGuardando] = useState(false)

  const cambiarPaso = (i: number, campo: keyof PasoAyuda, valor: string) =>
    setPasos((ps) => ps.map((p, j) => (j === i ? { ...p, [campo]: valor } : p)))
  const mover = (i: number, d: -1 | 1) =>
    setPasos((ps) => {
      const copia = [...ps]
      ;[copia[i], copia[i + d]] = [copia[i + d], copia[i]]
      return copia
    })

  const guardar = async () => {
    setGuardando(true)
    try {
      const r = await api.patch<ArticuloAyuda>(`/evaluacion/ayuda/${guia.slug}/`, {
        titulo, resumen, notas, publicado, pasos: pasos.filter((p) => p.titulo.trim()),
      })
      toast.success('Guía actualizada')
      alGuardar(r.data)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo guardar la guía'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Editar guía</DialogTitle>
        <DialogDescription>Describe el procedimiento tal como aparece en la plataforma.</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="guia-titulo">Título</Label>
          <Input id="guia-titulo" value={titulo} maxLength={150} onChange={(e) => setTitulo(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="guia-resumen">Resumen</Label>
          <Textarea id="guia-resumen" value={resumen} maxLength={300} rows={2} onChange={(e) => setResumen(e.target.value)} />
        </div>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Pasos</legend>
          {pasos.map((p, i) => (
            <div key={i} className="space-y-1.5 rounded-lg border border-border p-3">
              <div className="flex items-center gap-1.5">
                <span className="w-5 text-sm font-semibold text-muted-foreground">{i + 1}</span>
                <Input
                  value={p.titulo}
                  onChange={(e) => cambiarPaso(i, 'titulo', e.target.value)}
                  placeholder="Título del paso"
                  aria-label={`Título del paso ${i + 1}`}
                />
                <Button variant="ghost" size="sm" onClick={() => mover(i, -1)} disabled={i === 0} aria-label={`Subir paso ${i + 1}`}>
                  <ArrowUp className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => mover(i, 1)} disabled={i === pasos.length - 1} aria-label={`Bajar paso ${i + 1}`}>
                  <ArrowDown className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setPasos((ps) => ps.filter((_, j) => j !== i))} aria-label={`Quitar paso ${i + 1}`}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
              <Textarea
                value={p.detalle}
                rows={2}
                onChange={(e) => cambiarPaso(i, 'detalle', e.target.value)}
                placeholder="Detalle (opcional)"
                aria-label={`Detalle del paso ${i + 1}`}
              />
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={() => setPasos((ps) => [...ps, { titulo: '', detalle: '' }])} disabled={pasos.length >= 30}>
            <Plus className="mr-1.5 h-4 w-4" aria-hidden />
            Agregar paso
          </Button>
        </fieldset>
        <div className="space-y-1">
          <Label htmlFor="guia-notas">Notas</Label>
          <Textarea id="guia-notas" value={notas} rows={3} onChange={(e) => setNotas(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={publicado} onChange={(e) => setPublicado(e.target.checked)} className="h-4 w-4 accent-primary" />
          Publicada (visible para los roles de la guía)
        </label>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={alCerrar}>Cancelar</Button>
        <Button onClick={guardar} disabled={guardando || !titulo.trim() || !resumen.trim()}>
          {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
          Guardar
        </Button>
      </DialogFooter>
    </>
  )
}
