// Tarjeta de un simulacro del docente (HU-19).
//
// Muestra la configuracion, la distribucion y el estado de disponibilidad, y
// expone las acciones de editar, activar/desactivar y eliminar. Toda la
// identidad visual sale de la paleta institucional del modulo.

import { useState } from 'react'
import type { ReactNode } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  BarChart3,
  CalendarClock,
  ClipboardCheck,
  ClipboardList,
  Clock,
  Eye,
  ListChecks,
  Pencil,
  Power,
  Repeat,
  Trash2,
} from 'lucide-react'
import type { SimulacroSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

interface TarjetaSimulacroProps {
  simulacro: SimulacroSaberPro
  onVerPreguntas: (simulacro: SimulacroSaberPro) => void
  onVerResultados: (simulacro: SimulacroSaberPro) => void
  onRevisar: (simulacro: SimulacroSaberPro) => void
  onEditar: (simulacro: SimulacroSaberPro) => void
  onEliminar: (simulacro: SimulacroSaberPro) => void
  onCambiarActivo: (simulacro: SimulacroSaberPro) => void
}

function nombreCriterio(distribucion: SimulacroSaberPro['distribuciones'][number]): string {
  if (distribucion.afirmacion) return distribucion.afirmacion.nombre
  if (distribucion.competencia) return distribucion.competencia.nombre
  return `Parte ${distribucion.parte}`
}

export function TarjetaSimulacro({
  simulacro,
  onVerPreguntas,
  onVerResultados,
  onRevisar,
  onEditar,
  onEliminar,
  onCambiarActivo,
}: TarjetaSimulacroProps) {
  const esIngles = simulacro.area.nombre === 'Inglés'
  const esEscrita = simulacro.area.nombre === 'Comunicación Escrita'
  const fechaLimite = simulacro.fecha_limite ? new Date(simulacro.fecha_limite) : null
  const [ahora] = useState(() => Date.now())
  const vencido = fechaLimite !== null && fechaLimite.getTime() <= ahora

  return (
    <Card className={cn('relative flex h-full flex-col overflow-hidden', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <div aria-hidden="true" className={cn('h-1 w-full', paletaSaberPro.franja)} />
      <CardHeader className="gap-3 pb-3">
        <div className="flex items-start justify-between gap-2">
          <span className={cn('flex h-10 w-10 items-center justify-center rounded-xl', paletaSaberPro.iconoChip)}>
            <ClipboardList className="h-5 w-5" />
          </span>
          <div className="flex flex-wrap justify-end gap-1.5">
            <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
              {esIngles
                ? `${simulacro.distribuciones.length} parte${simulacro.distribuciones.length === 1 ? '' : 's'}`
                : simulacro.distribuciones.length > 0
                  ? `${simulacro.distribuciones.length} criterio${simulacro.distribuciones.length === 1 ? '' : 's'}`
                  : 'Banco completo'}
            </Badge>
            <Badge
              variant="outline"
              className={cn(
                'text-[10px]',
                simulacro.activo
                  ? 'border-[#1e3a5f]/30 text-[#1e3a5f] dark:border-[#E3C063]/50 dark:text-[#E3C063]'
                  : 'border-[#6b7a8d]/40 text-[#6b7a8d] dark:border-[#B9B2A2]/40 dark:text-[#B9B2A2]'
              )}
            >
              {simulacro.activo ? 'Activo' : 'Inactivo'}
            </Badge>
            {vencido && (
              <Badge
                variant="outline"
                className="border-[#b8432a]/30 text-[10px] text-[#b8432a] dark:border-[#F29A52]/40 dark:text-[#F29A52]"
              >
                Plazo vencido
              </Badge>
            )}
          </div>
        </div>
        <CardTitle className={cn('text-base font-bold leading-snug', paletaSaberPro.titulo)}>
          {simulacro.titulo || 'Simulacro sin titulo'}
        </CardTitle>
        {simulacro.descripcion && (
          <p className={cn('line-clamp-2 text-xs leading-relaxed', paletaSaberPro.texto)}>
            {simulacro.descripcion}
          </p>
        )}
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-3">
        <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          <Dato icono={<ListChecks className="h-3.5 w-3.5" />} etiqueta="Preguntas">
            {simulacro.total_preguntas}/{simulacro.num_preguntas}
          </Dato>
          <Dato icono={<Clock className="h-3.5 w-3.5" />} etiqueta="Tiempo">
            {simulacro.tiempo_limite_minutos} min
          </Dato>
          <Dato icono={<Repeat className="h-3.5 w-3.5" />} etiqueta="Intentos">
            {simulacro.intentos_maximos}
          </Dato>
          <Dato icono={<CalendarClock className="h-3.5 w-3.5" />} etiqueta="Cierra">
            {fechaLimite
              ? fechaLimite.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
              : 'Sin limite'}
          </Dato>
        </div>

        {esEscrita && (
          <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>
            Limite de palabras:{' '}
            <strong className={paletaSaberPro.titulo}>
              {simulacro.limite_palabras ?? 'sin limite'}
            </strong>
          </p>
        )}

        {simulacro.distribuciones.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {simulacro.distribuciones.map((distribucion) => (
              <span
                key={distribucion.id}
                className={cn(
                  'rounded-full border px-2 py-0.5 text-[10px]',
                  'border-[rgba(30,58,95,0.14)] text-[#2c3e50] dark:border-[rgba(243,237,225,0.18)] dark:text-[#CFC9BA]'
                )}
              >
                {esIngles ? `Parte ${distribucion.parte}` : `${nombreCriterio(distribucion)} · ${distribucion.cantidad}`}
              </span>
            ))}
          </div>
        )}

        <div className="mt-auto flex flex-wrap gap-1.5 border-t pt-3">
          {esEscrita && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className={cn('h-8 flex-1 gap-1.5 text-xs sm:flex-none', paletaSaberPro.accion)}
              onClick={() => onRevisar(simulacro)}
            >
              <ClipboardCheck className="h-3.5 w-3.5" /> Revisar respuestas
            </Button>
          )}
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn('h-8 flex-1 gap-1.5 text-xs sm:flex-none', paletaSaberPro.apoyoTitulo)}
            onClick={() => onVerResultados(simulacro)}
          >
            <BarChart3 className="h-3.5 w-3.5" /> Calificaciones
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn('h-8 flex-1 gap-1.5 text-xs sm:flex-none', paletaSaberPro.titulo)}
            onClick={() => onVerPreguntas(simulacro)}
          >
            <Eye className="h-3.5 w-3.5" /> Ver preguntas
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn('h-8 flex-1 gap-1.5 text-xs sm:flex-none', paletaSaberPro.titulo)}
            onClick={() => onEditar(simulacro)}
          >
            <Pencil className="h-3.5 w-3.5" /> Editar
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn('h-8 flex-1 gap-1.5 text-xs sm:flex-none', paletaSaberPro.texto)}
            onClick={() => onCambiarActivo(simulacro)}
          >
            <Power className="h-3.5 w-3.5" /> {simulacro.activo ? 'Desactivar' : 'Activar'}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="h-8 flex-1 gap-1.5 text-xs text-[#b8432a] hover:bg-[#b8432a]/10 hover:text-[#b8432a] dark:text-[#F29A52] sm:flex-none"
            onClick={() => onEliminar(simulacro)}
          >
            <Trash2 className="h-3.5 w-3.5" /> Eliminar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface DatoProps {
  icono: ReactNode
  etiqueta: string
  children: ReactNode
}

function Dato({ icono, etiqueta, children }: DatoProps) {
  return (
    <div className="rounded-lg bg-[#f3ede1]/70 px-2 py-1.5 dark:bg-[#172A45]/70">
      <p className={cn('flex items-center gap-1 text-[9px] uppercase tracking-[0.08em]', paletaSaberPro.apoyo)}>
        {icono} {etiqueta}
      </p>
      <p className={cn('mt-0.5 truncate text-[11px] font-semibold', paletaSaberPro.titulo)}>{children}</p>
    </div>
  )
}