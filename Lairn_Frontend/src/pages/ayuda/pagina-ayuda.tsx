// Centro de ayuda (ADR-018): guías de los procedimientos reales de la
// plataforma, filtradas por rol, con búsqueda (sin tildes) y categorías.

import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ChevronRight, Loader2, PlayCircle, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ListaAyuda } from '@/types/ayuda'

export default function PaginaAyuda() {
  const [params, setParams] = useSearchParams()
  const categoria = params.get('categoria') ?? ''
  const [busqueda, setBusqueda] = useState(params.get('q') ?? '')
  const [datos, setDatos] = useState<ListaAyuda | null>(null)
  const [error, setError] = useState(false)

  // La búsqueda se envía al servidor (incluye pasos y notas) con una pausa corta.
  useEffect(() => {
    const id = window.setTimeout(() => {
      api
        .get<ListaAyuda>('/evaluacion/ayuda/', { params: { q: busqueda || undefined, categoria: categoria || undefined } })
        .then((r) => {
          setDatos(r.data)
          setError(false)
        })
        .catch(() => setError(true))
    }, 250)
    return () => window.clearTimeout(id)
  }, [busqueda, categoria])

  const cambiar = (clave: string, valor: string) => {
    const nuevos = new URLSearchParams(params)
    if (valor) nuevos.set(clave, valor)
    else nuevos.delete(clave)
    setParams(nuevos, { replace: true })
  }

  const grupos = (datos?.articulos ?? []).reduce<Record<string, ListaAyuda['articulos']>>((acc, a) => {
    ;(acc[a.categoria_nombre] ??= []).push(a)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow="Centro de ayuda"
        titulo="¿Qué necesitas hacer?"
        subtitulo="Guías paso a paso de los procedimientos de la plataforma. Solo ves las de tu rol."
      />

      <div className="relative max-w-xl">
        <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <Input
          type="search"
          value={busqueda}
          onChange={(e) => {
            setBusqueda(e.target.value)
            cambiar('q', e.target.value)
          }}
          placeholder="Buscar: momento, docente, exportar, evaluación…"
          aria-label="Buscar en el centro de ayuda"
          className="pl-9"
        />
      </div>

      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Categorías">
        {[{ clave: '', nombre: 'Todas', total: undefined as number | undefined }, ...(datos?.categorias ?? [])].map((c) => (
          <button
            key={c.clave || 'todas'}
            type="button"
            onClick={() => cambiar('categoria', c.clave)}
            aria-pressed={categoria === c.clave}
            className={cn(
              'rounded-full border px-3 py-1.5 text-sm transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
              categoria === c.clave ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground hover:bg-muted',
            )}
          >
            {c.nombre}
            {c.total !== undefined && <span className="ml-1 opacity-70">{c.total}</span>}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-destructive">No se pudo cargar el centro de ayuda. Intenta de nuevo.</p>}
      {!datos && !error && (
        <div className="flex justify-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
        </div>
      )}
      {datos && !datos.articulos.length && (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No hay guías para “{busqueda}”{categoria ? ' en esta categoría' : ''}. Prueba con otra palabra.
          </CardContent>
        </Card>
      )}

      {Object.entries(grupos).map(([nombre, articulos]) => (
        <section key={nombre} className="space-y-2" aria-labelledby={`cat-${nombre}`}>
          <h2 id={`cat-${nombre}`} className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
            {nombre}
          </h2>
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {articulos.map((a) => (
              <li key={a.slug}>
                <Link
                  to={`/ayuda/${a.slug}`}
                  className="flex h-full flex-col gap-2 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                >
                  <span className="flex items-start justify-between gap-2">
                    <span className="font-medium text-foreground">{a.titulo}</span>
                    <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                  </span>
                  <span className="text-sm text-muted-foreground">{a.resumen}</span>
                  <span className="mt-auto flex flex-wrap gap-1.5 pt-1">
                    {a.tiene_video && (
                      <Badge variant="secondary" className="gap-1 font-normal">
                        <PlayCircle className="h-3 w-3" aria-hidden />
                        Video
                      </Badge>
                    )}
                    {!a.publicado && <Badge variant="warning" className="font-normal">No publicada</Badge>}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
