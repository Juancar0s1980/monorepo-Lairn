// Guía del centro de ayuda (ADR-018): pasos, notas, acceso a la pantalla y
// video. El video se pide con la sesión (no está publicado en /media).
// El Administrador edita la guía y sube o quita el video.

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, ArrowRight, Info, Loader2, Pencil, PlayCircle, Trash2, Upload, VideoOff } from 'lucide-react'
import { useAuth } from '@/context/contexto-auth/use-auth'
import { ROLES } from '@/types/usuario'
import type { ArticuloAyuda } from '@/types/ayuda'
import { mensajeError } from '@/pages/academico/academico-utils'
import { EditorGuia } from './componentes/editor-guia'

export default function PaginaGuiaAyuda() {
  const { slug = '' } = useParams()
  const { rol } = useAuth()
  const esAdmin = rol === ROLES.ADMIN
  const [guia, setGuia] = useState<ArticuloAyuda | null>(null)
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'no_encontrada'>('cargando')
  const [video, setVideo] = useState<string | null>(null)
  const [cargandoVideo, setCargandoVideo] = useState(false)
  const [editando, setEditando] = useState(false)
  const [subiendo, setSubiendo] = useState(false)
  const entradaVideo = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let vigente = true
    api
      .get<ArticuloAyuda>(`/evaluacion/ayuda/${slug}/`)
      .then((r) => {
        if (!vigente) return
        setGuia(r.data)
        setEstado('listo')
      })
      .catch(() => vigente && setEstado('no_encontrada'))
    return () => {
      vigente = false
    }
  }, [slug])

  // Libera el video descargado al salir o al cambiarlo.
  useEffect(() => () => {
    if (video) URL.revokeObjectURL(video)
  }, [video])

  const verVideo = async () => {
    setCargandoVideo(true)
    try {
      const r = await api.get<Blob>(`/evaluacion/ayuda/${slug}/video/`, { responseType: 'blob', timeout: 120000 })
      setVideo(URL.createObjectURL(r.data))
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo cargar el video'))
    } finally {
      setCargandoVideo(false)
    }
  }

  const subirVideo = async (archivo: File) => {
    const datos = new FormData()
    datos.append('video', archivo)
    setSubiendo(true)
    try {
      const r = await api.post<ArticuloAyuda>(`/evaluacion/ayuda/${slug}/video/`, datos, {
        headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000,
      })
      setGuia(r.data)
      setVideo(null)
      toast.success('Video actualizado')
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo subir el video'))
    } finally {
      setSubiendo(false)
      if (entradaVideo.current) entradaVideo.current.value = ''
    }
  }

  const quitarVideo = async () => {
    try {
      const r = await api.delete<ArticuloAyuda>(`/evaluacion/ayuda/${slug}/video/`)
      setGuia(r.data)
      setVideo(null)
      toast.success('Video quitado')
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo quitar el video'))
    }
  }

  if (estado === 'cargando') {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }
  if (estado === 'no_encontrada' || !guia) {
    return (
      <div className="space-y-4">
        <Link to="/ayuda" className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
          <ArrowLeft className="h-4 w-4" aria-hidden /> Centro de ayuda
        </Link>
        <p className="text-sm text-muted-foreground">Esta guía no existe o no está disponible para tu rol.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link to="/ayuda" className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
        <ArrowLeft className="h-4 w-4" aria-hidden /> Centro de ayuda
      </Link>

      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/ayuda?categoria=${guia.categoria}`}>
            <Badge variant="outline" className="font-normal">{guia.categoria_nombre}</Badge>
          </Link>
          {!guia.publicado && <Badge variant="warning" className="font-normal">No publicada</Badge>}
        </div>
        <h1 className="font-heading text-3xl text-balance text-foreground">{guia.titulo}</h1>
        <p className="text-muted-foreground">{guia.resumen}</p>
        <div className="flex flex-wrap gap-2 pt-1">
          {guia.ruta && (
            <Link
              to={guia.ruta}
              className="inline-flex h-8 items-center rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              Ir a la pantalla
              <ArrowRight className="ml-1.5 h-4 w-4" aria-hidden />
            </Link>
          )}
          {esAdmin && (
            <Button variant="outline" size="sm" onClick={() => setEditando(true)}>
              <Pencil className="mr-1.5 h-4 w-4" aria-hidden />
              Editar guía
            </Button>
          )}
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Video</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {guia.tiene_video ? (
            video ? (
              <video src={video} controls className="aspect-video w-full rounded-lg bg-black" aria-label={`Video: ${guia.titulo}`}>
                Tu navegador no puede reproducir este video.
              </video>
            ) : (
              <Button variant="outline" onClick={verVideo} disabled={cargandoVideo}>
                {cargandoVideo ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-1.5 h-4 w-4" aria-hidden />}
                Ver video
              </Button>
            )
          ) : (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <VideoOff className="h-4 w-4" aria-hidden />
              Esta guía todavía no tiene video. Sigue los pasos escritos.
            </p>
          )}
          {esAdmin && (
            <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3">
              <input
                ref={entradaVideo}
                type="file"
                accept=".mp4,.webm,video/mp4,video/webm"
                className="hidden"
                aria-label="Archivo de video (.mp4 o .webm)"
                onChange={(e) => {
                  const archivo = e.target.files?.[0]
                  if (archivo) void subirVideo(archivo)
                }}
              />
              <Button variant="outline" size="sm" onClick={() => entradaVideo.current?.click()} disabled={subiendo}>
                {subiendo ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Upload className="mr-1.5 h-4 w-4" aria-hidden />}
                {guia.tiene_video ? 'Reemplazar video' : 'Subir video'}
              </Button>
              {guia.tiene_video && (
                <Button variant="ghost" size="sm" onClick={quitarVideo}>
                  <Trash2 className="mr-1.5 h-4 w-4 text-destructive" aria-hidden />
                  Quitar video
                </Button>
              )}
              <span className="text-xs text-muted-foreground">
                .mp4 o .webm, máximo 100 MB.{guia.video_nombre ? ` Actual: ${guia.video_nombre}` : ''}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <section aria-labelledby="pasos-guia" className="space-y-3">
        <h2 id="pasos-guia" className="text-lg font-semibold text-foreground">Paso a paso</h2>
        <ol className="space-y-3">
          {(guia.pasos ?? []).map((p, i) => (
            <li key={i} className="flex gap-3 rounded-xl border border-border bg-card p-4">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground" aria-hidden>
                {i + 1}
              </span>
              <div className="min-w-0">
                <p className="font-medium text-foreground">{p.titulo}</p>
                {p.detalle && <p className="text-sm text-muted-foreground">{p.detalle}</p>}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {guia.notas && (
        <aside className="flex gap-2 rounded-xl border border-primary/40 bg-primary/5 p-4 text-sm">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
          <p className="text-foreground">{guia.notas}</p>
        </aside>
      )}

      <p className="text-xs text-muted-foreground">
        Actualizada el {new Date(guia.actualizado_en).toLocaleDateString('es-CO', { dateStyle: 'long' })}.
      </p>

      {esAdmin && (
        <EditorGuia
          abierto={editando}
          guia={guia}
          alCerrar={() => setEditando(false)}
          alGuardar={(g) => {
            setGuia(g)
            setEditando(false)
          }}
        />
      )}
    </div>
  )
}
