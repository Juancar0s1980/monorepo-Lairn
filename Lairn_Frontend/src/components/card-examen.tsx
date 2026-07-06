// Componente de card reutilizable para mostrar un examen con su estado de intentos.
//
// Card limpia con título, tema, badge de dificultad, stats compactas,
// indicador sutil de última nota y botón contextual.
//
// Uso:
//   <CardExamen
//     id={1}
//     cursoId={10}
//     titulo="Parcial 1"
//     tema="Álgebra lineal"
//     dificultad={2}
//     numPreguntas={20}
//     tiempo={60}
//     maxIntentos={3}
//     ultimaNota={4.2}
//     intentosUsados={1}
//   />

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { toast } from 'sonner'
import {
  Clock,
  HelpCircle,
  RotateCw,
  Play,
  RotateCcw,
  Ban,
  CheckCircle2,
  XCircle,
  Flag,
  Loader2,
  SignalLow,
  SignalMedium,
  SignalHigh,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

// Props del componente.
export interface CardExamenProps {
  id: number
  cursoId: number
  titulo: string
  tema: string
  dificultad: number
  numPreguntas: number
  tiempo: number
  maxIntentos: number
  /** Última nota obtenida por el estudiante en este examen. */
  ultimaNota?: number
  /** Número de intentos que ya usó el estudiante. */
  intentosUsados?: number
}

// Configuración visual de dificultad: label, color e icono.
const dificultadConfig: Record<
  number,
  { label: string; clase: string; icono: LucideIcon }
> = {
  1: {
    label: 'Básico',
    clase:
      'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800',
    icono: SignalLow,
  },
  2: {
    label: 'Intermedio',
    clase:
      'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
    icono: SignalMedium,
  },
  3: {
    label: 'Avanzado',
    clase:
      'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
    icono: SignalHigh,
  },
}

// Devuelve el color de la nota según su valor.
function colorNota(nota: number): string {
  if (nota >= 4.0) return 'text-emerald-600 dark:text-emerald-400'
  if (nota >= 3.0) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

export function CardExamen({
  id,
  cursoId,
  titulo,
  tema,
  dificultad,
  numPreguntas,
  tiempo,
  maxIntentos,
  ultimaNota,
  intentosUsados = 0,
}: CardExamenProps) {
  const navigate = useNavigate()
  const [reporteAbierto, setReporteAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [enviandoReporte, setEnviandoReporte] = useState(false)

  // Envía el reporte del examen al panel de moderación del administrador.
  const enviarReporte = async () => {
    if (!motivo.trim()) return
    setEnviandoReporte(true)
    try {
      await api.post('/moderacion/reportes/crear/', { examen: id, motivo })
      toast.success('Reporte enviado. El administrador lo revisará.')
      setMotivo('')
      setReporteAbierto(false)
    } catch {
      toast.error('No se pudo enviar el reporte')
    } finally {
      setEnviandoReporte(false)
    }
  }

  const dif = dificultadConfig[dificultad] || dificultadConfig[1]
  const IconoDificultad = dif.icono
  const tieneIntentos = intentosUsados > 0
  const intentosDisponibles = maxIntentos === 0
    ? true
    : intentosUsados < maxIntentos
  const aprobado = ultimaNota !== undefined && ultimaNota >= 3.0

  // Determina el estado del botón.
  const renderBoton = () => {
    if (!tieneIntentos) {
      return (
        <Button
          className="w-full"
          size="sm"
          onClick={() => navigate(`/mis-cursos/${cursoId}/examenes/${id}/rendir`)}
        >
          <Play className="h-4 w-4" />
          Rendir Examen
        </Button>
      )
    }

    if (!intentosDisponibles) {
      return (
        <Button className="w-full" size="sm" variant="outline" disabled>
          <Ban className="h-4 w-4" />
          Intentos Agotados
        </Button>
      )
    }

    return (
      <Button
        className="w-full"
        size="sm"
        variant="outline"
        onClick={() => navigate(`/mis-cursos/${cursoId}/examenes/${id}/rendir`)}
      >
        <RotateCcw className="h-4 w-4" />
        Reintentar
      </Button>
    )
  }

  return (
    <Card className="h-full flex flex-col transition-all hover:shadow-md hover:border-primary/30 group">
      <CardContent className="p-5 flex flex-col flex-1 gap-3">
        {/* Título + badge de dificultad */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-base line-clamp-1 group-hover:text-primary transition-colors">
              {titulo}
            </h3>
            <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
              {tema || 'Sin tema'}
            </p>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${dif.clase}`}
          >
            <IconoDificultad className="h-3 w-3" />
            {dif.label}
          </span>
        </div>

        {/* Stats compactas */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <HelpCircle className="h-3.5 w-3.5" />
            <span>{numPreguntas} preg.</span>
          </div>
          <div className="h-3 w-px bg-border" />
          <div className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            <span>{tiempo} min</span>
          </div>
          <div className="h-3 w-px bg-border" />
          <div className="flex items-center gap-1">
            <RotateCw className="h-3.5 w-3.5" />
            <span>
              {maxIntentos === 0
                ? 'Ilimitados'
                : `${maxIntentos - intentosUsados}/${maxIntentos}`}
            </span>
          </div>
        </div>

        {/* Estado de intentos previos — altura fija para alinear botones */}
        <div className="flex items-center gap-1.5 text-xs h-5">
          {tieneIntentos && (
            <>
              {aprobado ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-red-500" />
              )}
              <span className="text-muted-foreground">Última nota:</span>
              <span className={`font-medium ${colorNota(ultimaNota!)}`}>
                {ultimaNota!.toFixed(2)}
              </span>
            </>
          )}
        </div>

        {/* Botón contextual + reportar — siempre al fondo */}
        <div className="mt-auto flex items-center gap-2">
          <div className="flex-1">{renderBoton()}</div>
          <Button
            variant="ghost"
            size="icon-sm"
            className="shrink-0 text-muted-foreground hover:text-destructive"
            title="Reportar examen"
            onClick={() => setReporteAbierto(true)}
          >
            <Flag className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>

      {/* Diálogo para reportar el examen al administrador */}
      <Dialog
        open={reporteAbierto}
        onOpenChange={(open) => {
          if (!enviandoReporte) {
            setReporteAbierto(open)
            if (!open) setMotivo('')
          }
        }}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Reportar Examen</DialogTitle>
            <DialogDescription>
              Cuéntale al administrador qué problema encontraste en{' '}
              <span className="font-medium text-foreground">{titulo}</span>.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Ej: la pregunta 3 tiene la respuesta correcta mal marcada"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            maxLength={500}
            rows={4}
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setReporteAbierto(false)}
              disabled={enviandoReporte}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={enviarReporte}
              disabled={enviandoReporte || !motivo.trim()}
            >
              {enviandoReporte ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Enviando...
                </div>
              ) : (
                'Enviar Reporte'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
