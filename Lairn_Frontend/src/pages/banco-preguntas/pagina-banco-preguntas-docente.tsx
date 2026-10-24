// Banco de preguntas del docente (Módulo 2: HU-04 y HU-05).
//
// 1. Generar con IA: el docente elige su asignatura (plan de aula), el
//    resultado de aprendizaje y, opcional, una competencia transversal.
//    Las preguntas llegan "Pendientes de validación" (no visibles a estudiantes).
// 2. Curaduría: revisar, editar, aprobar (pasa al banco oficial) o descartar.
// 3. Filtrar el banco por estado y competencia transversal (HU-04.5).
//
// Solo aparecen las asignaturas que la coordinación vinculó a un curso del docente.

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { AlertCircle, BookOpenCheck, Loader2, RotateCcw, Sparkles } from 'lucide-react'
import type { EstadoPregunta } from '@/types/banco'
import { useBancoPreguntas } from './use-banco-preguntas'
import { TarjetaPregunta } from './componentes/tarjeta-pregunta'
import { DialogosPregunta } from './componentes/dialogos-pregunta'

const ESTADOS: { valor: EstadoPregunta; etiqueta: string; vacio: string }[] = [
  {
    valor: 'pendiente',
    etiqueta: 'Pendientes de validación',
    vacio: 'No hay preguntas por revisar. Genera nuevas con IA en el panel de arriba.',
  },
  { valor: 'aprobada', etiqueta: 'Banco oficial', vacio: 'Aún no has aprobado preguntas en esta asignatura.' },
  { valor: 'descartada', etiqueta: 'Descartadas', vacio: 'No hay preguntas descartadas.' },
]

const CANTIDADES = [1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: `${n} pregunta${n > 1 ? 's' : ''}` }))

export default function PaginaBancoPreguntasDocente() {
  const bp = useBancoPreguntas()
  const a = bp.asignatura

  if (bp.cargandoAsignaturas) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  const encabezado = (
    <EncabezadoPagina
      eyebrow="Panel del docente"
      titulo="Banco de preguntas"
      subtitulo="Genera preguntas con IA a partir de tus resultados de aprendizaje, revísalas y aprueba las que formarán parte del banco oficial."
    />
  )

  if (bp.errorCarga) {
    return (
      <div className="space-y-6">
        {encabezado}
        <Card>
          <CardContent className="flex flex-col items-start gap-3 p-6">
            <p role="alert" className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" aria-hidden />
              {bp.errorCarga}
            </p>
            <Button variant="outline" onClick={bp.cargarAsignaturas}>
              <RotateCcw className="mr-1.5 h-4 w-4" aria-hidden />
              Reintentar
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!bp.asignaturas.length) {
    return (
      <div className="space-y-6">
        {encabezado}
        <Card>
          <CardContent className="space-y-2 p-6 text-sm">
            <BookOpenCheck className="h-8 w-8 text-primary" aria-hidden />
            <p className="font-medium text-foreground">Aún no tienes asignaturas asignadas</p>
            <p className="text-muted-foreground">
              Para usar el banco, la coordinación académica debe vincular tu curso a una asignatura
              de la malla (Configuración académica → Malla → editar asignatura → Docente).
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const puedeGenerar = !!bp.resultadoId && !bp.generando
  const estadoActual = ESTADOS.find((e) => e.valor === bp.estado) ?? ESTADOS[0]

  return (
    <div className="space-y-6">
      {encabezado}

      {/* Asignatura activa: aplica a la generación y al listado */}
      <Card>
        <CardHeader className="flex flex-col gap-3 space-y-0 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base">Asignatura</CardTitle>
            <CardDescription>{a ? `${a.programa.nombre} · curso ${a.curso.nombre}` : ''}</CardDescription>
          </div>
          <Select
            value={bp.asignaturaId}
            onValueChange={(v) => v && bp.elegirAsignatura(v)}
            items={bp.asignaturas.map((x) => ({ value: String(x.id), label: `${x.codigo} — ${x.nombre}` }))}
          >
            <SelectTrigger className="w-full sm:w-[340px]" aria-label="Asignatura">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {bp.asignaturas.map((x) => (
                <SelectItem key={x.id} value={String(x.id)}>
                  {x.codigo} — {x.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
      </Card>

      {/* Generación con IA (HU-04.1 / 04.2) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden />
            Generar preguntas con IA
          </CardTitle>
          <CardDescription>
            La IA crea casos contextualizados a partir del resultado de aprendizaje de tu plan de aula.
            Llegan como pendientes y nadie más las ve hasta que las apruebes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {a && !a.resultados.length ? (
            <p className="text-sm text-muted-foreground">
              Esta asignatura aún no tiene resultados de aprendizaje. La coordinación los registra en
              Configuración académica (o al aprobar el plan de aula).
            </p>
          ) : (
            <form
              className="grid gap-4 md:grid-cols-[2fr_1.3fr_auto_auto] md:items-end"
              onSubmit={(e) => {
                e.preventDefault()
                void bp.generar()
              }}
            >
              <div className="min-w-0 space-y-1.5">
                <Label htmlFor="banco-ra">
                  Resultado de aprendizaje <span className="text-destructive" aria-hidden="true">*</span>
                </Label>
                <Select
                  value={bp.resultadoId}
                  onValueChange={(v) => bp.setResultadoId(v ?? '')}
                  items={(a?.resultados ?? []).map((r) => ({ value: String(r.id), label: r.descripcion }))}
                >
                  <SelectTrigger id="banco-ra" className="w-full">
                    <SelectValue placeholder="Elige el RA a evaluar" />
                  </SelectTrigger>
                  <SelectContent>
                    {(a?.resultados ?? []).map((r) => (
                      <SelectItem key={r.id} value={String(r.id)}>
                        {r.descripcion}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="min-w-0 space-y-1.5">
                <Label htmlFor="banco-competencia">Competencia transversal (opcional)</Label>
                <Select
                  value={bp.competenciaId || 'ninguna'}
                  onValueChange={(v) => bp.setCompetenciaId(v && v !== 'ninguna' ? v : '')}
                  items={[
                    { value: 'ninguna', label: 'Ninguna' },
                    ...(a?.competencias_transversales ?? []).map((c) => ({ value: String(c.id), label: c.nombre })),
                  ]}
                >
                  <SelectTrigger id="banco-competencia" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ninguna">Ninguna</SelectItem>
                    {(a?.competencias_transversales ?? []).map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="banco-cantidad">Cantidad</Label>
                <Select
                  value={String(bp.cantidad)}
                  onValueChange={(v) => bp.setCantidad(Number(v ?? 3))}
                  items={CANTIDADES}
                >
                  <SelectTrigger id="banco-cantidad" className="w-full md:w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CANTIDADES.map((c) => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" disabled={!puedeGenerar}>
                {bp.generando ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <Sparkles className="mr-1.5 h-4 w-4" aria-hidden />
                )}
                {bp.generando ? 'Generando…' : 'Generar'}
              </Button>
              {bp.generando && (
                <p role="status" className="text-xs text-muted-foreground md:col-span-4">
                  La IA está redactando las preguntas; puede tardar hasta un minuto.
                </p>
              )}
            </form>
          )}
        </CardContent>
      </Card>

      {/* Curaduría y banco (HU-05 / HU-04.5) */}
      <div className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <Tabs value={bp.estado} onValueChange={(v) => bp.setEstado(v as EstadoPregunta)}>
            <TabsList className="flex w-full justify-start overflow-x-auto overflow-y-hidden bg-muted md:w-auto md:overflow-visible">
              {ESTADOS.map((e) => (
                <TabsTrigger key={e.valor} value={e.valor}>
                  {e.etiqueta}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <Select
            value={bp.filtroCompetencia || 'todas'}
            onValueChange={(v) => bp.setFiltroCompetencia(v && v !== 'todas' ? v : '')}
            items={[
              { value: 'todas', label: 'Todas las competencias' },
              ...(a?.competencias_transversales ?? []).map((c) => ({ value: String(c.id), label: c.nombre })),
            ]}
          >
            <SelectTrigger className="w-full md:w-[260px]" aria-label="Filtrar por competencia transversal">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todas">Todas las competencias</SelectItem>
              {(a?.competencias_transversales ?? []).map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {bp.cargandoPreguntas ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando preguntas" />
          </div>
        ) : bp.preguntas.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              {bp.filtroCompetencia ? 'Ninguna pregunta coincide con el filtro.' : estadoActual.vacio}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground" aria-live="polite">
              {bp.preguntas.length} pregunta{bp.preguntas.length > 1 ? 's' : ''}
            </p>
            {bp.preguntas.map((p) => (
              <TarjetaPregunta key={p.id} p={p} bp={bp} />
            ))}
          </div>
        )}
      </div>

      <DialogosPregunta bp={bp} />
    </div>
  )
}
