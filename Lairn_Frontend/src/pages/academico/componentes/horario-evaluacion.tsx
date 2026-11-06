// Horario de la evaluación formal (HU-06.3): fecha, hora de inicio, duración y
// tolerancia para llegar tarde. El cierre ya no se escribe: se calcula como
// inicio + duración + tolerancia (ver `horario-utils.ts`).
//
// - Fecha: atajos Hoy / Mañana / Pasado mañana o un día cualquiera.
// - Hora: desplegable de sugerencias cada 30 min (hoy solo futuras desde la
//   siguiente hora exacta) u "Otra hora" con un reloj (hora, minutos, a. m./p. m.).
// - Duración: 1 h, 1 h 30 (predeterminada), 2 h u Otra (horas 0-10, minutos 0/15/30/45).
// - Tolerancia: 0, 10, 15 (predeterminada) o 30 min.
// Se monta con `key` por evaluación: el modo "Otra" se deduce de los valores guardados.

import { useEffect, useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CalendarClock, Clock, Sun, Moon } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  DURACIONES_PRESET,
  DURACION_MAXIMA,
  DURACION_MINIMA,
  TOLERANCIAS_PRESET,
  fechaLocal,
  hora12,
  resumenHorario,
  sugerenciasHora,
  sumarDias,
  textoDuracion,
} from '../horario-utils'

export interface ValorHorario {
  fecha: string
  hora: string
  duracion_minutos: number
  tolerancia_minutos: number
}

const ATAJOS = [
  { dias: 0, texto: 'Hoy' },
  { dias: 1, texto: 'Mañana' },
  { dias: 2, texto: 'Pasado mañana' },
]
const MINUTOS_OTRA = [0, 15, 30, 45]
const HORAS_RELOJ = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
const MINUTOS_RELOJ = Array.from({ length: 12 }, (_, i) => i * 5)
const dos = (n: number) => String(n).padStart(2, '0')

// Reloj para cuadrar una hora distinta de las sugeridas: hora (1-12),
// minutos (de 5 en 5) y a. m./p. m. Cada cambio actualiza la hora del formulario.
function RelojHora({ hora, onChange }: { hora: string; onChange: (hhmm: string) => void }) {
  const [h24, min] = hora ? hora.split(':').map(Number) : [7, 0]
  const pm = h24 >= 12
  const h12 = h24 % 12 === 0 ? 12 : h24 % 12
  // Un minuto guardado que no sea múltiplo de 5 se conserva como opción.
  const minutos = MINUTOS_RELOJ.includes(min) ? MINUTOS_RELOJ : [...MINUTOS_RELOJ, min].sort((a, b) => a - b)
  const fijar = (nh12: number, nmin: number, npm: boolean) => onChange(`${dos((nh12 % 12) + (npm ? 12 : 0))}:${dos(nmin)}`)

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-muted/30 p-3">
      <div className="flex items-center gap-2">
        <Clock className="h-5 w-5 text-primary" aria-hidden />
        <span className="font-mono text-2xl font-semibold text-foreground tabular-nums" aria-live="polite">
          {h12}:{dos(min)} <span className="text-base">{pm ? 'p. m.' : 'a. m.'}</span>
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <Select
          value={String(h12)}
          onValueChange={(v) => v !== null && fijar(Number(v), min, pm)}
          items={HORAS_RELOJ.map((h) => ({ value: String(h), label: String(h) }))}
        >
          <SelectTrigger className="w-20" aria-label="Hora">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {HORAS_RELOJ.map((h) => (
              <SelectItem key={h} value={String(h)}>
                {h}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-lg font-semibold text-muted-foreground" aria-hidden>:</span>
        <Select
          value={String(min)}
          onValueChange={(v) => v !== null && fijar(h12, Number(v), pm)}
          items={minutos.map((m) => ({ value: String(m), label: dos(m) }))}
        >
          <SelectTrigger className="w-20" aria-label="Minutos">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {minutos.map((m) => (
              <SelectItem key={m} value={String(m)}>
                {dos(m)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div role="group" aria-label="Mañana o tarde" className="flex gap-1">
          <Opcion activo={!pm} onClick={() => fijar(h12, min, false)}>
            <span className="flex items-center gap-1"><Sun className="h-3.5 w-3.5" aria-hidden />a. m.</span>
          </Opcion>
          <Opcion activo={pm} onClick={() => fijar(h12, min, true)}>
            <span className="flex items-center gap-1"><Moon className="h-3.5 w-3.5" aria-hidden />p. m.</span>
          </Opcion>
        </div>
      </div>
    </div>
  )
}

// Botón de opción (chip) con estado accesible.
function Opcion({
  activo,
  destacado,
  onClick,
  children,
  etiqueta,
}: {
  activo: boolean
  destacado?: boolean
  onClick: () => void
  children: React.ReactNode
  etiqueta?: string
}) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      aria-label={etiqueta}
      onClick={onClick}
      className={cn(
        'rounded-lg border px-2.5 py-1.5 text-sm transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
        activo
          ? 'border-primary bg-primary text-primary-foreground'
          : destacado
            ? 'border-border font-medium text-foreground hover:bg-muted'
            : 'border-border text-muted-foreground hover:bg-muted',
      )}
    >
      {children}
    </button>
  )
}

export function HorarioEvaluacion({ valor, onChange }: { valor: ValorHorario; onChange: (cambio: Partial<ValorHorario>) => void }) {
  // "Ahora" se refresca cada minuto para que las sugerencias de hoy no ofrezcan horas pasadas.
  const [ahora, setAhora] = useState(() => new Date())
  useEffect(() => {
    const id = window.setInterval(() => setAhora(new Date()), 60_000)
    return () => window.clearInterval(id)
  }, [])

  const [duracionOtra, setDuracionOtra] = useState(() => !DURACIONES_PRESET.includes(valor.duracion_minutos))
  const [toleranciaOtra, setToleranciaOtra] = useState(() => !TOLERANCIAS_PRESET.includes(valor.tolerancia_minutos))
  // "Otra hora" (reloj) si la hora guardada no está entre las sugeridas del día.
  const [horaOtra, setHoraOtra] = useState(() => {
    const lista = sugerenciasHora(valor.fecha || fechaLocal(new Date()), new Date())
    return lista.length === 0 || (!!valor.hora && !lista.includes(valor.hora))
  })

  const hoy = fechaLocal(ahora)
  const sugerencias = sugerenciasHora(valor.fecha || hoy, ahora)
  const horaEnLista = sugerencias.includes(valor.hora)
  const verReloj = horaOtra || sugerencias.length === 0
  const resumen = resumenHorario(valor.fecha, valor.hora, valor.duracion_minutos, valor.tolerancia_minutos)
  const inicioPasado = resumen ? resumen.inicio.getTime() < ahora.getTime() : false

  const horasOtra = Math.floor(valor.duracion_minutos / 60)
  const minutosOtra = valor.duracion_minutos % 60
  // Un valor guardado con minutos fuera de 0/15/30/45 se conserva como opción extra.
  const opcionesMinutos = MINUTOS_OTRA.includes(minutosOtra) ? MINUTOS_OTRA : [...MINUTOS_OTRA, minutosOtra].sort((a, b) => a - b)
  const duracionInvalida = valor.duracion_minutos < DURACION_MINIMA || valor.duracion_minutos > DURACION_MAXIMA

  const abrirReloj = () => {
    setHoraOtra(true)
    // El reloj parte de la hora elegida o de la primera sugerida.
    if (!valor.hora) onChange({ hora: sugerencias[0] ?? '07:00' })
  }

  return (
    <div className="space-y-5">
      {/* Fecha */}
      <div className="space-y-2">
        <Label htmlFor="ef-fecha">
          Fecha <span className="text-destructive" aria-hidden="true">*</span>
        </Label>
        <div className="flex flex-wrap items-center gap-2">
          {ATAJOS.map((a) => {
            const f = fechaLocal(sumarDias(ahora, a.dias))
            return (
              <Opcion key={a.dias} activo={valor.fecha === f} onClick={() => onChange({ fecha: f })}>
                {a.texto}
              </Opcion>
            )
          })}
          <Input
            id="ef-fecha"
            type="date"
            min={hoy}
            value={valor.fecha}
            onChange={(e) => onChange({ fecha: e.target.value })}
            className="w-auto min-w-0"
            aria-label="Otra fecha"
          />
        </div>
      </div>

      {/* Hora de inicio */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground" id="ef-hora-titulo">
          Hora de inicio <span className="text-destructive" aria-hidden="true">*</span>
        </p>
        <div role="group" aria-labelledby="ef-hora-titulo" className="flex flex-wrap gap-1.5">
          <Opcion activo={!verReloj} onClick={() => setHoraOtra(false)}>
            Hora sugerida
          </Opcion>
          <Opcion activo={verReloj} onClick={abrirReloj}>
            Otra hora
          </Opcion>
        </div>
        {verReloj ? (
          <>
            {sugerencias.length === 0 && (
              <p className="text-xs text-muted-foreground">Ya no quedan horas sugeridas para hoy: cuadra la hora en el reloj o elige otro día.</p>
            )}
            <RelojHora hora={valor.hora} onChange={(hora) => onChange({ hora })} />
          </>
        ) : (
          <Select
            value={horaEnLista ? valor.hora : null}
            onValueChange={(v) => v && onChange({ hora: v })}
            items={sugerencias.map((h) => ({ value: h, label: hora12(h) }))}
          >
            <SelectTrigger className="w-full sm:w-56" aria-label="Hora de inicio sugerida">
              <SelectValue placeholder="Elige una hora" />
            </SelectTrigger>
            <SelectContent>
              {sugerencias.map((h) => (
                <SelectItem key={h} value={h}>
                  {/* Las horas exactas se destacan; las medias horas van más tenues. */}
                  <span className={h.endsWith(':00') ? 'font-medium text-foreground' : 'text-muted-foreground'}>{hora12(h)}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {!verReloj && valor.hora && !horaEnLista && (
          <p className="text-xs text-muted-foreground">
            La hora guardada ({hora12(valor.hora)}) no está entre las sugeridas: elige una o usa "Otra hora".
          </p>
        )}
      </div>

      {/* Duración */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground" id="ef-duracion-titulo">Duración del intento</p>
        <div role="group" aria-labelledby="ef-duracion-titulo" className="flex flex-wrap gap-1.5">
          {DURACIONES_PRESET.map((m) => (
            <Opcion
              key={m}
              activo={!duracionOtra && valor.duracion_minutos === m}
              onClick={() => {
                setDuracionOtra(false)
                onChange({ duracion_minutos: m })
              }}
            >
              {textoDuracion(m)}
            </Opcion>
          ))}
          <Opcion activo={duracionOtra} onClick={() => setDuracionOtra(true)}>
            Otra
          </Opcion>
        </div>
        {duracionOtra && (
          <div className="flex flex-wrap items-center gap-2">
            <Select
              value={String(horasOtra)}
              onValueChange={(v) => v !== null && onChange({ duracion_minutos: Number(v) * 60 + minutosOtra })}
              items={Array.from({ length: 11 }, (_, h) => ({ value: String(h), label: `${h} h` }))}
            >
              <SelectTrigger className="w-24" aria-label="Horas de duración">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 11 }, (_, h) => (
                  <SelectItem key={h} value={String(h)}>
                    {h} h
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={String(minutosOtra)}
              onValueChange={(v) => v !== null && onChange({ duracion_minutos: horasOtra * 60 + Number(v) })}
              items={opcionesMinutos.map((m) => ({ value: String(m), label: `${m} min` }))}
            >
              <SelectTrigger className="w-28" aria-label="Minutos de duración">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {opcionesMinutos.map((m) => (
                  <SelectItem key={m} value={String(m)}>
                    {m} min
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {duracionInvalida && (
              <span role="alert" className="text-xs text-destructive">
                Debe estar entre {DURACION_MINIMA} min y {textoDuracion(DURACION_MAXIMA)}.
              </span>
            )}
          </div>
        )}
      </div>

      {/* Tolerancia */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground" id="ef-tolerancia-titulo">Tolerancia para llegar tarde</p>
        <p className="text-xs text-muted-foreground">
          Quien inicia dentro de este margen tiene su tiempo completo. El cierre se calcula solo.
        </p>
        <div role="group" aria-labelledby="ef-tolerancia-titulo" className="flex flex-wrap items-center gap-1.5">
          {TOLERANCIAS_PRESET.map((m) => (
            <Opcion
              key={m}
              activo={!toleranciaOtra && valor.tolerancia_minutos === m}
              onClick={() => {
                setToleranciaOtra(false)
                onChange({ tolerancia_minutos: m })
              }}
            >
              {m} min
            </Opcion>
          ))}
          <Opcion activo={toleranciaOtra} onClick={() => setToleranciaOtra(true)}>
            Otra
          </Opcion>
          {toleranciaOtra && (
            <Input
              type="number"
              min={0}
              max={600}
              value={valor.tolerancia_minutos}
              onChange={(e) => onChange({ tolerancia_minutos: Math.max(0, Math.min(600, Number(e.target.value) || 0)) })}
              aria-label="Tolerancia en minutos"
              className="w-24"
            />
          )}
        </div>
      </div>

      {/* Resumen */}
      <div
        role="status"
        aria-live="polite"
        className={cn(
          'flex items-start gap-2 rounded-lg p-3 text-sm',
          inicioPasado ? 'bg-warning/15 text-foreground' : 'bg-primary/5 text-foreground',
        )}
      >
        {resumen ? <CalendarClock className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden /> : <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />}
        <span>
          {resumen ? resumen.texto : 'Elige la fecha y la hora de inicio para ver el horario.'}
          {inicioPasado && <span className="block text-xs">La hora de inicio ya pasó.</span>}
        </span>
      </div>
    </div>
  )
}
