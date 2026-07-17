// Tab de objetivos de aprendizaje del curso (vista del docente).
//
// Permite gestionar los objetivos que anclan la generación de exámenes:
//   - Agregar a mano (input + botón).
//   - Sugerir con IA: pide borradores al backend, el docente marca cuáles
//     aceptar y solo esos se guardan (la IA nunca guarda directo).
//   - Editar en línea y eliminar cada objetivo.
//
// Endpoints: GET/POST /examenes/cursos/{id}/objetivos/,
//            POST /examenes/cursos/{id}/objetivos/sugerir/,
//            PATCH/DELETE /examenes/cursos/{id}/objetivos/{objetivoId}/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Check, Loader2, Pencil, Plus, Sparkles, Target, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'
import type { ObjetivoCurso } from '@/types/examen'

interface TabObjetivosDocenteProps {
  cursoId: string
}

export function TabObjetivosDocente({ cursoId }: TabObjetivosDocenteProps) {
  const [objetivos, setObjetivos] = useState<ObjetivoCurso[]>([])
  const [cargando, setCargando] = useState(true)

  // Alta manual.
  const [nuevoTexto, setNuevoTexto] = useState('')
  const [creando, setCreando] = useState(false)

  // Edición en línea.
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [textoEdicion, setTextoEdicion] = useState('')
  const [guardandoEdicion, setGuardandoEdicion] = useState(false)

  // Sugerencias de IA (modal de curación).
  const [sugerencias, setSugerencias] = useState<string[]>([])
  const [seleccionadas, setSeleccionadas] = useState<Set<number>>(new Set())
  const [modalSugerencias, setModalSugerencias] = useState(false)
  const [sugiriendo, setSugiriendo] = useState(false)
  const [aceptando, setAceptando] = useState(false)

  // Carga inicial de objetivos.
  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<ObjetivoCurso[]>(
          `/examenes/cursos/${cursoId}/objetivos/`,
          { signal: controlador.signal }
        )
        setObjetivos(data)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudieron cargar los objetivos')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId])

  // Crea un objetivo (manual o sugerencia aceptada).
  const crearObjetivo = async (descripcion: string): Promise<ObjetivoCurso | null> => {
    const { data } = await api.post<ObjetivoCurso>(
      `/examenes/cursos/${cursoId}/objetivos/`,
      { descripcion, orden: objetivos.length + 1 }
    )
    return data
  }

  const agregarManual = async () => {
    const texto = nuevoTexto.trim()
    if (!texto) return
    setCreando(true)
    try {
      const creado = await crearObjetivo(texto)
      if (creado) setObjetivos((prev) => [...prev, creado])
      setNuevoTexto('')
      toast.success('Objetivo agregado')
    } catch {
      toast.error('No se pudo agregar el objetivo')
    } finally {
      setCreando(false)
    }
  }

  // Pide sugerencias a la IA y abre el modal de curación.
  const pedirSugerencias = async () => {
    setSugiriendo(true)
    try {
      const { data } = await api.post<{ sugerencias: string[] }>(
        `/examenes/cursos/${cursoId}/objetivos/sugerir/`
      )
      setSugerencias(data.sugerencias)
      setSeleccionadas(new Set(data.sugerencias.map((_, i) => i)))
      setModalSugerencias(true)
    } catch {
      toast.error('La IA no pudo generar sugerencias, intenta de nuevo')
    } finally {
      setSugiriendo(false)
    }
  }

  // Guarda las sugerencias marcadas como objetivos reales.
  const aceptarSeleccionadas = async () => {
    const elegidas = sugerencias.filter((_, i) => seleccionadas.has(i))
    if (elegidas.length === 0) {
      setModalSugerencias(false)
      return
    }
    setAceptando(true)
    try {
      const creados: ObjetivoCurso[] = []
      for (const texto of elegidas) {
        const creado = await crearObjetivo(texto)
        if (creado) creados.push(creado)
      }
      setObjetivos((prev) => [...prev, ...creados])
      toast.success(`${creados.length} objetivo(s) agregado(s)`)
      setModalSugerencias(false)
    } catch {
      toast.error('No se pudieron guardar todas las sugerencias')
    } finally {
      setAceptando(false)
    }
  }

  const guardarEdicion = async () => {
    if (editandoId === null) return
    const texto = textoEdicion.trim()
    if (!texto) return
    setGuardandoEdicion(true)
    try {
      const { data } = await api.patch<ObjetivoCurso>(
        `/examenes/cursos/${cursoId}/objetivos/${editandoId}/`,
        { descripcion: texto }
      )
      setObjetivos((prev) => prev.map((o) => (o.id === editandoId ? data : o)))
      setEditandoId(null)
      toast.success('Objetivo actualizado')
    } catch {
      toast.error('No se pudo actualizar el objetivo')
    } finally {
      setGuardandoEdicion(false)
    }
  }

  const eliminarObjetivo = async (id: number) => {
    try {
      await api.delete(`/examenes/cursos/${cursoId}/objetivos/${id}/`)
      setObjetivos((prev) => prev.filter((o) => o.id !== id))
      toast.success('Objetivo eliminado')
    } catch {
      toast.error('No se pudo eliminar el objetivo')
    }
  }

  const alternarSeleccion = (i: number) => {
    setSeleccionadas((prev) => {
      const nuevo = new Set(prev)
      if (nuevo.has(i)) nuevo.delete(i)
      else nuevo.add(i)
      return nuevo
    })
  }

  if (cargando) {
    return (
      <div className="flex h-[30vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Explicación + acciones */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground max-w-prose">
          Los exámenes anclados a estos objetivos generan preguntas que evalúan
          exactamente lo que definas aquí, sin desviarse del temario.
        </p>
        <Button onClick={pedirSugerencias} disabled={sugiriendo} variant="outline" className="shrink-0">
          {sugiriendo ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generando...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Sugerir con IA
            </>
          )}
        </Button>
      </div>

      {/* Alta manual */}
      <div className="flex gap-2">
        <Input
          placeholder='Ej: "Aplicar la regla de la cadena en funciones compuestas"'
          value={nuevoTexto}
          maxLength={200}
          onChange={(e) => setNuevoTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              agregarManual()
            }
          }}
        />
        <Button onClick={agregarManual} disabled={creando || !nuevoTexto.trim()} className="shrink-0">
          {creando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Agregar
        </Button>
      </div>

      {/* Estado vacío */}
      {objetivos.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Target className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Este curso aún no tiene objetivos
          </p>
          <p className="text-xs text-muted-foreground">
            Agrégalos a mano o pide sugerencias a la IA
          </p>
        </div>
      )}

      {/* Lista de objetivos */}
      {objetivos.length > 0 && (
        <Card>
          <CardContent className="divide-y p-0">
            {objetivos.map((objetivo, indice) => (
              <div key={objetivo.id} className="flex items-center gap-3 px-4 py-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {indice + 1}
                </span>

                {editandoId === objetivo.id ? (
                  <>
                    <Input
                      value={textoEdicion}
                      maxLength={200}
                      onChange={(e) => setTextoEdicion(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          guardarEdicion()
                        }
                        if (e.key === 'Escape') setEditandoId(null)
                      }}
                      autoFocus
                    />
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="shrink-0 text-emerald-600"
                      onClick={guardarEdicion}
                      disabled={guardandoEdicion}
                    >
                      {guardandoEdicion ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    </Button>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="shrink-0 text-muted-foreground"
                      onClick={() => setEditandoId(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <p className="flex-1 text-sm">{objetivo.descripcion}</p>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="shrink-0 text-muted-foreground hover:text-foreground"
                      title="Editar"
                      onClick={() => {
                        setEditandoId(objetivo.id)
                        setTextoEdicion(objetivo.descripcion)
                      }}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="shrink-0 text-muted-foreground hover:text-destructive"
                      title="Eliminar"
                      onClick={() => eliminarObjetivo(objetivo.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Modal de curación de sugerencias de IA */}
      <Dialog open={modalSugerencias} onOpenChange={(open) => !aceptando && setModalSugerencias(open)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Sugerencias de la IA
            </DialogTitle>
            <DialogDescription>
              Marca las que quieras agregar como objetivos del curso. Puedes editarlas después.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            {sugerencias.map((sugerencia, i) => (
              <button
                key={i}
                type="button"
                onClick={() => alternarSeleccion(i)}
                className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left text-sm transition-colors ${
                  seleccionadas.has(i)
                    ? 'border-primary bg-primary/5'
                    : 'border-border text-muted-foreground'
                }`}
              >
                <span
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                    seleccionadas.has(i) ? 'border-primary bg-primary text-primary-foreground' : 'border-input'
                  }`}
                >
                  {seleccionadas.has(i) && <Check className="h-3 w-3" />}
                </span>
                {sugerencia}
              </button>
            ))}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalSugerencias(false)} disabled={aceptando}>
              Descartar
            </Button>
            <Button onClick={aceptarSeleccionadas} disabled={aceptando || seleccionadas.size === 0}>
              {aceptando ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                `Agregar ${seleccionadas.size} objetivo(s)`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
