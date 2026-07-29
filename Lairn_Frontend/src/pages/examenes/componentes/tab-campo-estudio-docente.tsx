// Tab de Campo de Estudio del curso (vista del docente).
//
// Permite:
//   - Activar/desactivar la función para el curso (switch).
//   - Generar temas de estudio con IA: a diferencia de "Sugerir con IA" en
//     Objetivos, aquí los borradores SÍ se guardan de inmediato como
//     "pendiente" (cola de revisión, no un modal efímero).
//   - Aprobar, editar o eliminar cada tema antes de que el estudiante lo vea.
//
// Endpoints: PATCH /campo-estudio/cursos/{id}/activar/,
//            GET/POST /campo-estudio/cursos/{id}/temas/(generar/),
//            PATCH/DELETE /campo-estudio/temas/{temaId}/,
//            PATCH /campo-estudio/temas/{temaId}/aprobar/.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Check, Lightbulb, Loader2, Pencil, Sparkles, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import type { TemaEstudio } from '@/types/campo-estudio'

interface TabCampoEstudioDocenteProps {
  cursoId: string
  habilitado: boolean
}

export function TabCampoEstudioDocente({ cursoId, habilitado: habilitadoInicial }: TabCampoEstudioDocenteProps) {
  const [habilitado, setHabilitado] = useState(habilitadoInicial)
  const [cambiandoHabilitado, setCambiandoHabilitado] = useState(false)

  const [temas, setTemas] = useState<TemaEstudio[]>([])
  const [cargando, setCargando] = useState(true)
  const [generando, setGenerando] = useState(false)

  const [temaEnEdicion, setTemaEnEdicion] = useState<TemaEstudio | null>(null)
  const [tituloEdicion, setTituloEdicion] = useState('')
  const [contenidoEdicion, setContenidoEdicion] = useState('')
  const [guardandoEdicion, setGuardandoEdicion] = useState(false)

  const [aprobandoId, setAprobandoId] = useState<number | null>(null)
  const [eliminandoId, setEliminandoId] = useState<number | null>(null)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<TemaEstudio[]>(
          `/campo-estudio/cursos/${cursoId}/temas/`,
          { signal: controlador.signal }
        )
        setTemas(data)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudieron cargar los temas de estudio')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId])

  const alternarHabilitado = async (valor: boolean) => {
    setCambiandoHabilitado(true)
    try {
      await api.patch(`/campo-estudio/cursos/${cursoId}/activar/`, { habilitado: valor })
      setHabilitado(valor)
      toast.success(valor ? 'Campo de Estudio activado' : 'Campo de Estudio desactivado')
    } catch {
      toast.error('No se pudo cambiar el estado del Campo de Estudio')
    } finally {
      setCambiandoHabilitado(false)
    }
  }

  const generarConIA = async () => {
    setGenerando(true)
    try {
      const { data } = await api.post<TemaEstudio[]>(
        `/campo-estudio/cursos/${cursoId}/temas/generar/`
      )
      setTemas((prev) => [...data, ...prev])
      toast.success(`${data.length} tema(s) generado(s), listos para revisar`)
    } catch {
      toast.error('La IA no pudo generar temas, intenta de nuevo')
    } finally {
      setGenerando(false)
    }
  }

  const abrirEdicion = (tema: TemaEstudio) => {
    setTemaEnEdicion(tema)
    setTituloEdicion(tema.titulo)
    setContenidoEdicion(tema.contenido)
  }

  const guardarEdicion = async () => {
    if (!temaEnEdicion) return
    const titulo = tituloEdicion.trim()
    const contenido = contenidoEdicion.trim()
    if (!titulo || !contenido) return

    setGuardandoEdicion(true)
    try {
      const { data } = await api.patch<TemaEstudio>(
        `/campo-estudio/temas/${temaEnEdicion.id}/`,
        { titulo, contenido }
      )
      setTemas((prev) => prev.map((t) => (t.id === data.id ? data : t)))
      setTemaEnEdicion(null)
      toast.success('Tema actualizado')
    } catch {
      toast.error('No se pudo actualizar el tema')
    } finally {
      setGuardandoEdicion(false)
    }
  }

  const aprobarTema = async (id: number) => {
    setAprobandoId(id)
    try {
      const { data } = await api.patch<TemaEstudio>(`/campo-estudio/temas/${id}/aprobar/`)
      setTemas((prev) => prev.map((t) => (t.id === id ? data : t)))
      toast.success('Tema aprobado: ya es visible para los estudiantes')
    } catch {
      toast.error('No se pudo aprobar el tema')
    } finally {
      setAprobandoId(null)
    }
  }

  const eliminarTema = async (id: number) => {
    setEliminandoId(id)
    try {
      await api.delete(`/campo-estudio/temas/${id}/`)
      setTemas((prev) => prev.filter((t) => t.id !== id))
      toast.success('Tema eliminado')
    } catch {
      toast.error('No se pudo eliminar el tema')
    } finally {
      setEliminandoId(null)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-[30vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const pendientes = temas.filter((t) => t.estado === 'pendiente')
  const aprobados = temas.filter((t) => t.estado === 'aprobado')

  return (
    <div className="space-y-4">
      {/* Activar/desactivar + explicación */}
      <div className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
            <Lightbulb className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-medium">Campo de Estudio</p>
            <p className="text-sm text-muted-foreground max-w-prose">
              Los estudiantes inscritos podrán ver los temas que apruebes y
              seguir preguntándole a la IA sobre cada uno, sin salir de este curso.
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 pl-12 sm:pl-0">
          <span className="text-xs text-muted-foreground">
            {habilitado ? 'Activado' : 'Desactivado'}
          </span>
          <Switch
            checked={habilitado}
            onCheckedChange={alternarHabilitado}
            disabled={cambiandoHabilitado}
          />
        </div>
      </div>

      {/* Acción de generación */}
      <div className="flex justify-end">
        <Button onClick={generarConIA} disabled={generando} variant="outline">
          {generando ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generando...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generar temas con IA
            </>
          )}
        </Button>
      </div>

      {/* Estado vacío */}
      {temas.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Lightbulb className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Este curso aún no tiene temas de estudio
          </p>
          <p className="text-xs text-muted-foreground">
            Genera borradores con IA y aprueba los que quieras publicar
          </p>
        </div>
      )}

      {/* Pendientes de revisión */}
      {pendientes.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            Pendientes de revisión ({pendientes.length})
          </p>
          <Card>
            <CardContent className="divide-y p-0">
              {pendientes.map((tema) => (
                <div key={tema.id} className="flex items-start gap-3 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{tema.titulo}</p>
                    <p className="line-clamp-2 text-xs text-muted-foreground">{tema.contenido}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="text-muted-foreground hover:text-foreground"
                      title="Editar"
                      onClick={() => abrirEdicion(tema)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="text-emerald-600 hover:text-emerald-700"
                      title="Aprobar"
                      onClick={() => aprobarTema(tema.id)}
                      disabled={aprobandoId === tema.id}
                    >
                      {aprobandoId === tema.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="text-muted-foreground hover:text-destructive"
                      title="Eliminar"
                      onClick={() => eliminarTema(tema.id)}
                      disabled={eliminandoId === tema.id}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Publicados para estudiantes */}
      {aprobados.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            Publicados para estudiantes ({aprobados.length})
          </p>
          <Card>
            <CardContent className="divide-y p-0">
              {aprobados.map((tema) => (
                <div key={tema.id} className="flex items-start gap-3 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{tema.titulo}</p>
                    <p className="line-clamp-2 text-xs text-muted-foreground">{tema.contenido}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <Badge variant="outline" className="text-emerald-600 border-emerald-600/30">
                      Aprobado
                    </Badge>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="text-muted-foreground hover:text-foreground"
                      title="Editar"
                      onClick={() => abrirEdicion(tema)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      className="text-muted-foreground hover:text-destructive"
                      title="Retirar"
                      onClick={() => eliminarTema(tema.id)}
                      disabled={eliminandoId === tema.id}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Diálogo de edición */}
      <Dialog open={temaEnEdicion !== null} onOpenChange={(open) => !open && setTemaEnEdicion(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Editar tema de estudio</DialogTitle>
            <DialogDescription>
              Ajusta el título o el contenido antes de aprobarlo (o después, si ya está publicado).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="titulo-tema">Título</Label>
              <Input
                id="titulo-tema"
                maxLength={150}
                value={tituloEdicion}
                onChange={(e) => setTituloEdicion(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contenido-tema">Contenido</Label>
              <Textarea
                id="contenido-tema"
                rows={10}
                value={contenidoEdicion}
                onChange={(e) => setContenidoEdicion(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setTemaEnEdicion(null)} disabled={guardandoEdicion}>
              Cancelar
            </Button>
            <Button
              onClick={guardarEdicion}
              disabled={guardandoEdicion || !tituloEdicion.trim() || !contenidoEdicion.trim()}
            >
              {guardandoEdicion ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                'Guardar cambios'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
