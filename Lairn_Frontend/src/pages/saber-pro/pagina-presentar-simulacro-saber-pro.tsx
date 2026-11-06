// Página de presentación cronometrada de un simulacro Saber Pro (HU-21 y HU-22).
//
// Flujo:
//   1. inicia o reanuda el intento con `usePresentacionSimulacroSaberPro`;
//   2. muestra un único bloque a la vez y no permite retroceder;
//   3. envía la respuesta del bloque actual al backend;
//   4. finaliza automáticamente cuando el contador llega a 0.
//   5. aplica el modo seguro de HU-22 (copiar/pegar, foco y pantalla completa).
//
// El backend nunca envía respuestas correctas. La calificación y el resultado
// final llegan recién cuando el intento termina.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  Clock,
  FileText,
  GraduationCap,
  Languages,
  ListChecks,
  Loader2,
  Send,
  ShieldCheck,
  Trophy,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { usePresentacionSimulacroSaberPro } from '@/hooks/use-presentacion-simulacro-saber-pro'
import { useProteccionExamen } from '@/hooks/use-proteccion-examen'
import { solicitarPantallaCompleta } from '@/utilities/pantalla-completa'
import { AvisoProteccionSimulacro } from './componentes/aviso-proteccion-simulacro'
import type {
  DatosRespuestaPresentacion,
  EstadoPresentacionSaberPro,
  PreguntaPresentacionSaberPro,
  ResultadoPresentacionSaberPro,
} from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import {
  paletaSaberPro,
  selectContenidoAncho,
  selectItemLargo,
  selectTriggerLargo,
} from './utilidades'

const LETRAS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

function letraOpcion(indice: number): string {
  return LETRAS[indice] ?? String(indice + 1)
}

function formatearTiempo(segundos: number): string {
  const minutos = Math.floor(segundos / 60)
  const restantes = segundos % 60
  return `${String(minutos).padStart(2, '0')}:${String(restantes).padStart(2, '0')}`
}

function mensajeMotivo(resultado: ResultadoPresentacionSaberPro): string {
  if (resultado.motivo_finalizacion === 'tiempo_agotado') {
    return 'El tiempo del simulacro se agotó y tus respuestas se enviaron automáticamente.'
  }
  if (resultado.motivo_finalizacion === 'fecha_limite') {
    return 'La fecha límite del simulacro venció y tus respuestas se enviaron automáticamente.'
  }
  if (resultado.motivo_finalizacion === 'manual') {
    return 'Finalizaste el simulacro antes de que se agotara el tiempo.'
  }
  return 'Completaste todos los bloques del simulacro.'
}

function CargandoPresentacion() {
  return (
    <div className={cn('flex min-h-[60vh] flex-col items-center justify-center gap-3 rounded-2xl border p-10', paletaSaberPro.banda, paletaSaberPro.borde)}>
      <Loader2 className={cn('h-9 w-9 animate-spin', paletaSaberPro.accion)} />
      <p className={cn('text-sm', paletaSaberPro.texto)}>Preparando tu simulacro...</p>
    </div>
  )
}

function ErrorPresentacion({
  mensaje,
  reintentar,
  onVolver,
}: {
  mensaje: string
  reintentar: () => void
  onVolver?: () => void
}) {
  return (
    <div className={cn('flex min-h-[50vh] flex-col items-center justify-center gap-4 rounded-2xl border p-10 text-center', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <span className={cn('flex h-14 w-14 items-center justify-center rounded-full', paletaSaberPro.chipAccion)}>
        <AlertCircle className="h-7 w-7" />
      </span>
      <p className={cn('max-w-md text-sm font-medium', paletaSaberPro.titulo)}>{mensaje}</p>
      <div className="flex flex-wrap justify-center gap-2">
        <Button type="button" className={paletaSaberPro.botonAccion} onClick={reintentar}>
          Reintentar
        </Button>
        {onVolver && (
          <Button type="button" className={paletaSaberPro.botonNeutro} onClick={onVolver}>
            Volver a mis simulacros
          </Button>
        )}
      </div>
    </div>
  )
}

function ContadorSimulacro({
  presentacion,
  onAgotado,
}: {
  presentacion: EstadoPresentacionSaberPro
  onAgotado: () => void
}) {
  const [segundos, setSegundos] = useState(presentacion.tiempo_restante_segundos)
  const agotadoRef = useRef(false)

  useEffect(() => {
    if (presentacion.finalizada) return
    const calcular = () =>
      Math.max(
        0,
        Math.ceil((new Date(presentacion.expira_en).getTime() - Date.now()) / 1000)
      )
    const intervalo = window.setInterval(() => {
      const restante = calcular()
      setSegundos(restante)
      if (restante <= 0 && !agotadoRef.current) {
        agotadoRef.current = true
        onAgotado()
      }
    }, 1000)
    return () => window.clearInterval(intervalo)
  }, [onAgotado, presentacion.expira_en, presentacion.finalizada])

  const urgente = segundos <= 60
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-xl px-4 py-2.5 font-mono text-lg font-bold tabular-nums',
        urgente
          ? 'bg-[#b8432a]/12 text-[#b8432a] dark:bg-[#F29A52]/20 dark:text-[#F29A52]'
          : paletaSaberPro.chipGold
      )}
      role="timer"
      aria-live="off"
    >
      <Clock className="h-5 w-5" />
      {formatearTiempo(segundos)}
    </div>
  )
}

function OpcionMultiple({
  opciones,
  seleccionada,
  onSeleccionar,
  deshabilitada,
}: {
  opciones: string[]
  seleccionada: string | null
  onSeleccionar: (opcion: string) => void
  deshabilitada: boolean
}) {
  return (
    <div className="grid gap-2.5" role="radiogroup" aria-label="Opciones de respuesta">
      {opciones.map((opcion, indice) => {
        const activa = seleccionada === opcion
        return (
          <button
            key={`${indice}-${opcion}`}
            type="button"
            role="radio"
            aria-checked={activa}
            disabled={deshabilitada}
            onClick={() => onSeleccionar(opcion)}
            className={cn(
              'flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-60',
              activa
                ? 'border-[#e8740e] bg-[#e8740e]/10 dark:border-[#F29A52] dark:bg-[#F29A52]/15'
                : cn(paletaSaberPro.borde, 'bg-[#f3ede1]/60 hover:bg-[#ede6d8] dark:bg-[#172A45]/60 dark:hover:bg-[#1E3351]')
            )}
          >
            <span
              className={cn(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-bold',
                activa
                  ? 'border-[#e8740e] bg-[#e8740e] text-white dark:border-[#F29A52] dark:bg-[#F29A52] dark:text-[#172A45]'
                  : cn(paletaSaberPro.borde, paletaSaberPro.apoyo)
              )}
            >
              {letraOpcion(indice)}
            </span>
            <span className={cn('pt-0.5 text-sm leading-relaxed', paletaSaberPro.texto)}>{opcion}</span>
          </button>
        )
      })}
    </div>
  )
}

function ContenidoPregunta({
  pregunta,
  opcion,
  relaciones,
  respuestasBloque,
  texto,
  deshabilitado,
  onOpcion,
  onRelacion,
  onRespuestaBloque,
  onTexto,
}: {
  pregunta: PreguntaPresentacionSaberPro
  opcion: string | null
  relaciones: Record<string, string>
  respuestasBloque: Record<number, string>
  texto: string
  deshabilitado: boolean
  onOpcion: (valor: string) => void
  onRelacion: (descripcion: string, valor: string) => void
  onRespuestaBloque: (preguntaId: number, valor: string) => void
  onTexto: (valor: string) => void
}) {
  if (pregunta.subtipo === 'relacionar') {
    return (
      <div className="space-y-5">
        <div className={cn('rounded-xl border p-4', paletaSaberPro.borde, paletaSaberPro.bandaAlterna)}>
          <p className={cn('mb-2 text-xs font-semibold uppercase tracking-[0.12em]', paletaSaberPro.apoyoTitulo)}>
            Palabras disponibles
          </p>
          <div className="grid gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
            {pregunta.opciones.map((palabra, indice) => (
              <p key={`${indice}-${palabra}`} className={cn('text-sm', paletaSaberPro.texto)}>
                <span className={cn('mr-1 font-bold', paletaSaberPro.titulo)}>{letraOpcion(indice)}.</span>
                {palabra}
              </p>
            ))}
          </div>
        </div>

        <p className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>
          {pregunta.enunciado || 'Relaciona cada descripción con la palabra que corresponde.'}
        </p>

        <div className="space-y-3">
          {pregunta.descripciones.map((descripcion, indice) => (
            <div key={descripcion} className={cn('grid gap-2 rounded-xl border p-3 md:grid-cols-[1fr_240px] md:items-center', paletaSaberPro.borde)}>
              <p className={cn('text-sm leading-relaxed', paletaSaberPro.texto)}>
                <span className={cn('mr-2 font-bold', paletaSaberPro.titulo)}>{indice + 1}.</span>
                {descripcion}
              </p>
              <Select
                items={pregunta.opciones.map((palabra, i) => ({
                  value: palabra,
                  label: `${letraOpcion(i)}. ${palabra}`,
                }))}
                value={relaciones[descripcion] ?? ''}
                onValueChange={(valor) => onRelacion(descripcion, valor ?? '')}
                disabled={deshabilitado}
              >
                <SelectTrigger className={selectTriggerLargo}>
                  <SelectValue placeholder="Selecciona una palabra" />
                </SelectTrigger>
                <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                  {pregunta.opciones.map((palabra, i) => (
                    <SelectItem key={`${i}-${palabra}`} value={palabra} className={selectItemLargo}>
                      {letraOpcion(i)}. {palabra}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>
        <p className={cn('text-xs', paletaSaberPro.apoyo)}>
          Cada palabra se usa una sola vez. Hay más palabras que descripciones.
        </p>
      </div>
    )
  }

  if (pregunta.subtipo === 'bloque_ingles') {
    return (
      <div className="space-y-5">
        {pregunta.contexto && (
          <div className={cn('max-h-72 overflow-y-auto rounded-xl border p-4', paletaSaberPro.borde, paletaSaberPro.bandaAlterna)}>
            <p className={cn('whitespace-pre-wrap text-sm leading-relaxed', paletaSaberPro.texto)}>{pregunta.contexto}</p>
          </div>
        )}

        {pregunta.enunciado && (
          <p className={cn('text-sm font-medium leading-relaxed', paletaSaberPro.titulo)}>{pregunta.enunciado}</p>
        )}

        <div className="space-y-5">
          {pregunta.preguntas.map((interna) => (
            <div key={interna.id} className={cn('rounded-xl border p-4', paletaSaberPro.borde)}>
              <p className={cn('text-sm font-medium leading-relaxed', paletaSaberPro.titulo)}>
                <span className="mr-2 text-[#e8740e] dark:text-[#F29A52]">{interna.id}.</span>
                {interna.enunciado}
              </p>
              <div className="mt-3">
                <OpcionMultiple
                  opciones={interna.opciones}
                  seleccionada={respuestasBloque[interna.id] ?? null}
                  onSeleccionar={(valor) => onRespuestaBloque(interna.id, valor)}
                  deshabilitada={deshabilitado}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

    if (pregunta.subtipo === 'consigna') {
    const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0
    const limite = pregunta.limite_palabras
    const excede = limite != null && palabras > limite
    return (
      <div className="space-y-5">
        {pregunta.tema && (
          <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
            {pregunta.tema}
          </Badge>
        )}
        {pregunta.contexto && (
          <div className={cn('whitespace-pre-wrap rounded-xl border p-4 text-sm leading-relaxed', paletaSaberPro.borde, paletaSaberPro.bandaAlterna, paletaSaberPro.texto)}>
            {pregunta.contexto}
          </div>
        )}
        <p className={cn('text-sm font-medium leading-relaxed', paletaSaberPro.titulo)}>{pregunta.enunciado}</p>
        <div className="space-y-1.5">
          <label htmlFor="respuesta-consigna" className={cn('text-xs font-semibold', paletaSaberPro.titulo)}>
            Tu respuesta
          </label>
          <Textarea
            id="respuesta-consigna"
            value={texto}
            onChange={(evento) => onTexto(evento.target.value)}
            disabled={deshabilitado}
            placeholder="Escribe aquí tu texto argumentativo..."
            className="min-h-56 resize-y bg-white text-sm dark:bg-[#172A45]"
          />
          <p
            className={cn(
              'text-right text-[11px]',
              excede ? 'font-semibold text-[#b8432a] dark:text-[#F29A52]' : paletaSaberPro.apoyo
            )}
          >
            {palabras}
            {limite != null ? ` / ${limite}` : ''} palabras
            {excede ? ' · reduce tu texto para poder enviarlo' : ''}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {pregunta.contexto && (
        <div className={cn('whitespace-pre-wrap rounded-xl border p-4 text-sm leading-relaxed', paletaSaberPro.borde, paletaSaberPro.bandaAlterna, paletaSaberPro.texto)}>
          {pregunta.contexto}
        </div>
      )}
      <p className={cn('text-sm font-medium leading-relaxed', paletaSaberPro.titulo)}>{pregunta.enunciado}</p>
      <OpcionMultiple
        opciones={pregunta.opciones}
        seleccionada={opcion}
        onSeleccionar={onOpcion}
        deshabilitada={deshabilitado}
      />
    </div>
  )
}

function VistaResultado({
  presentacion,
  resultado,
  onVolver,
}: {
  presentacion: EstadoPresentacionSaberPro
  resultado: ResultadoPresentacionSaberPro
  onVolver: () => void
}) {
  const soloPendiente = resultado.revision_pendiente && resultado.total_evaluables === 0
  return (
    <div className={cn('relative overflow-hidden rounded-2xl border', paletaSaberPro.banda, paletaSaberPro.borde)}>
      <div aria-hidden="true" className={cn('h-2 w-full', paletaSaberPro.franja)} />
      <div className="relative p-6 md:p-10">
        <div className="mx-auto max-w-2xl text-center">
          <span className={cn('mx-auto flex h-16 w-16 items-center justify-center rounded-full', paletaSaberPro.chipGold)}>
            <Trophy className="h-8 w-8" />
          </span>
          <p className={cn('mt-4 text-[11px] font-semibold uppercase tracking-[0.18em]', paletaSaberPro.apoyoTitulo)}>
            Simulacro finalizado
          </p>
          <h1 className={cn('mt-1 text-2xl font-bold tracking-tight md:text-3xl', paletaSaberPro.titulo)}>
            {presentacion.simulacro_titulo || 'Resultado del simulacro'}
          </h1>
          <p className={cn('mt-2 text-sm', paletaSaberPro.texto)}>{mensajeMotivo(resultado)}</p>

          <div className={cn('mx-auto mt-6 flex h-40 w-40 flex-col items-center justify-center rounded-full border-4', paletaSaberPro.borde, paletaSaberPro.superficie)}>
            {soloPendiente ? (
              <span className={cn('px-3 text-sm font-bold', paletaSaberPro.titulo)}>
                Pendiente de revisión
              </span>
            ) : (
              <>
                <span className={cn('text-4xl font-black', paletaSaberPro.titulo)}>
                  {resultado.calificacion.toFixed(1)}
                </span>
                <span className={cn('text-[11px] uppercase tracking-[0.12em]', paletaSaberPro.apoyo)}>
                  {resultado.revision_pendiente ? 'parcial de 5.0' : 'de 5.0'}
                </span>
              </>
            )}
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className={cn('rounded-xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
              <p className={cn('text-[10px] uppercase tracking-[0.1em]', paletaSaberPro.apoyo)}>Correctas</p>
              <p className={cn('mt-1 text-xl font-bold', paletaSaberPro.titulo)}>
                {resultado.correctas}/{resultado.total_evaluables}
              </p>
            </div>
            <div className={cn('rounded-xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
              <p className={cn('text-[10px] uppercase tracking-[0.1em]', paletaSaberPro.apoyo)}>Bloques</p>
              <p className={cn('mt-1 text-xl font-bold', paletaSaberPro.titulo)}>
                {resultado.contenidos_respondidos}/{resultado.total_preguntas}
              </p>
            </div>
            <div className={cn('rounded-xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
              <p className={cn('text-[10px] uppercase tracking-[0.1em]', paletaSaberPro.apoyo)}>Ítems</p>
              <p className={cn('mt-1 text-xl font-bold', paletaSaberPro.titulo)}>{resultado.total_items}</p>
            </div>
          </div>

          {resultado.revision_pendiente && (
            <div className={cn('mt-5 flex items-start gap-2 rounded-xl border p-3 text-left text-xs', paletaSaberPro.borde, paletaSaberPro.bandaAlterna)}>
              <FileText className={cn('mt-0.5 h-4 w-4 shrink-0', paletaSaberPro.accion)} />
              <p className={paletaSaberPro.texto}>
                Tu consigna escrita está pendiente de revisión docente. La nota se actualizará cuando
                sea calificada.
              </p>
            </div>
          )}

          {resultado.calificacion_docente !== null && (
            <div
              className={cn(
                'mt-4 rounded-xl border p-4 text-left',
                paletaSaberPro.superficie,
                paletaSaberPro.borde
              )}
            >
              <p className={cn('text-xs font-semibold uppercase tracking-[0.1em]', paletaSaberPro.apoyoTitulo)}>
                Calificación del docente · {resultado.calificacion_docente.toFixed(1)} / 5.0
              </p>
              {resultado.retroalimentacion_docente && (
                <p className={cn('mt-2 whitespace-pre-wrap text-sm', paletaSaberPro.texto)}>
                  {resultado.retroalimentacion_docente}
                </p>
              )}
            </div>
          )}

          <Button type="button" className={cn('mt-7 gap-2', paletaSaberPro.botonAccion)} onClick={onVolver}>
            <ArrowLeft className="h-4 w-4" /> Volver a mis simulacros
          </Button>
        </div>
      </div>
    </div>
  )
}

function FormularioPregunta({
  presentacion,
  pregunta,
  enviando,
  onResponder,
}: {
  presentacion: EstadoPresentacionSaberPro
  pregunta: PreguntaPresentacionSaberPro
  enviando: boolean
  onResponder: (datos: DatosRespuestaPresentacion) => Promise<boolean>
}) {
  const [opcion, setOpcion] = useState<string | null>(null)
  const [relaciones, setRelaciones] = useState<Record<string, string>>({})
  const [respuestasBloque, setRespuestasBloque] = useState<Record<number, string>>({})
  const [texto, setTexto] = useState('')

  const puedeEnviar = useMemo(() => {
    if (enviando) return false
    if (pregunta.subtipo === 'opcion_multiple') return Boolean(opcion)
        if (pregunta.subtipo === 'consigna') {
      const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0
      return (
        palabras > 0 &&
        (pregunta.limite_palabras == null || palabras <= pregunta.limite_palabras)
      )
    }
    if (pregunta.subtipo === 'relacionar') {
      const valores = pregunta.descripciones.map((descripcion) => relaciones[descripcion])
      return valores.every(Boolean) && new Set(valores).size === valores.length
    }
    return pregunta.preguntas.every((interna) => Boolean(respuestasBloque[interna.id]))
  }, [enviando, opcion, pregunta, relaciones, respuestasBloque, texto])

  const enviarRespuesta = useCallback(async () => {
    if (!puedeEnviar) return
    let datos: DatosRespuestaPresentacion = { pregunta_id: pregunta.id }

    if (pregunta.subtipo === 'opcion_multiple') {
      datos = { ...datos, opcion: opcion ?? '' }
    } else if (pregunta.subtipo === 'consigna') {
      datos = { ...datos, texto }
    } else if (pregunta.subtipo === 'relacionar') {
      datos = {
        ...datos,
        relaciones: pregunta.descripciones.map((descripcion) => ({
          descripcion,
          respuesta: relaciones[descripcion] ?? '',
        })),
      }
    } else {
      datos = {
        ...datos,
        respuestas: pregunta.preguntas.map((interna) => respuestasBloque[interna.id] ?? ''),
      }
    }

    await onResponder(datos)
  }, [onResponder, opcion, puedeEnviar, pregunta, relaciones, respuestasBloque, texto])

  return (
    <Card className={cn('gap-0 overflow-hidden py-0', paletaSaberPro.superficie, paletaSaberPro.borde)}>
      <div aria-hidden="true" className={cn('h-1 w-full', paletaSaberPro.franja)} />
      <CardHeader className="gap-2 border-b px-5 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className={cn('flex h-9 w-9 items-center justify-center rounded-lg', paletaSaberPro.iconoChip)}>
            {pregunta.subtipo === 'consigna' ? (
              <FileText className="h-4 w-4" />
            ) : pregunta.subtipo === 'relacionar' || pregunta.subtipo === 'bloque_ingles' ? (
              <Languages className="h-4 w-4" />
            ) : (
              <ClipboardList className="h-4 w-4" />
            )}
          </span>
          <CardTitle className={cn('text-base font-bold', paletaSaberPro.titulo)}>
            {pregunta.subtipo === 'bloque_ingles'
              ? `Parte ${pregunta.parte ?? ''} de Inglés`
              : pregunta.subtipo === 'relacionar'
                ? 'Relaciona las descripciones'
                : pregunta.subtipo === 'consigna'
                  ? 'Consigna de escritura'
                  : 'Pregunta de selección múltiple'}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-5">
        <ContenidoPregunta
          pregunta={pregunta}
          opcion={opcion}
          relaciones={relaciones}
          respuestasBloque={respuestasBloque}
          texto={texto}
          deshabilitado={enviando}
          onOpcion={setOpcion}
          onRelacion={(descripcion, valor) =>
            setRelaciones((previas) => ({ ...previas, [descripcion]: valor }))
          }
          onRespuestaBloque={(internaId, valor) =>
            setRespuestasBloque((previas) => ({ ...previas, [internaId]: valor }))
          }
          onTexto={setTexto}
        />
      </CardContent>
      <div className={cn('flex flex-col-reverse gap-2 border-t px-5 py-4 sm:flex-row sm:items-center sm:justify-between', paletaSaberPro.bandaAlterna)}>
        <p className={cn('text-[11px]', paletaSaberPro.apoyo)}>
          No puedes volver a un bloque anterior.
        </p>
        <Button
          type="button"
          disabled={!puedeEnviar}
          className={cn('h-10 gap-2 sm:min-w-48', paletaSaberPro.botonAccion)}
          onClick={() => void enviarRespuesta()}
        >
          {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          {presentacion.contenidos_respondidos + 1 >= presentacion.total_preguntas
            ? 'Enviar y finalizar'
            : 'Enviar y continuar'}
        </Button>
      </div>
    </Card>
  )
}

export default function PaginaPresentarSimulacroSaberPro() {
  const { simulacroId } = useParams<{ simulacroId: string }>()
  const navegar = useNavigate()
  const idSimulacro = useMemo(() => {
    if (!simulacroId || !/^\d+$/.test(simulacroId)) return null
    return Number(simulacroId)
  }, [simulacroId])

  const {
    presentacion,
    cargando,
    enviando,
    error,
    responder,
    finalizar,
    bloquear,
    desbloquear,
    reintentar,
  } = usePresentacionSimulacroSaberPro(idSimulacro)

  const [codigoDesbloqueo, setCodigoDesbloqueo] = useState('')
  const [errorDesbloqueo, setErrorDesbloqueo] = useState<string | null>(null)

  const pregunta = presentacion?.pregunta ?? null
  const resultado = presentacion?.resultado ?? null
  const finalizada = presentacion?.finalizada ?? false
  const requiereCodigo = presentacion?.requiere_codigo_desbloqueo ?? false

  const manejarSalida = useCallback(() => {
    if (presentacion?.requiere_codigo_desbloqueo) void bloquear()
  }, [bloquear, presentacion?.requiere_codigo_desbloqueo])

  const { fueraDeFoco, reiniciarProteccion } = useProteccionExamen({
    activo: Boolean(presentacion) && !finalizada,
    onSalida: manejarSalida,
  })

  const bloqueada = Boolean(presentacion?.bloqueada) || fueraDeFoco

  const manejarDesbloqueo = useCallback(async () => {
    const codigo = codigoDesbloqueo.trim()
    if (!codigo) {
      setErrorDesbloqueo('Ingresa el código que te entregó tu docente.')
      return
    }

    solicitarPantallaCompleta()
    setErrorDesbloqueo(null)
    const resultadoDesbloqueo = await desbloquear(codigo)
    if (resultadoDesbloqueo.ok) {
      setCodigoDesbloqueo('')
      reiniciarProteccion()
      return
    }
    setErrorDesbloqueo(
      resultadoDesbloqueo.error ?? 'No se pudo desbloquear el examen. Intenta de nuevo.'
    )
  }, [codigoDesbloqueo, desbloquear, reiniciarProteccion])

  const volverAlExamen = useCallback(() => {
    setErrorDesbloqueo(null)
    reiniciarProteccion()
  }, [reiniciarProteccion])

  const volver = useCallback(() => navegar('/saber-pro/simulacros'), [navegar])

  if (idSimulacro === null) {
    return (
      <ErrorPresentacion
        mensaje="El simulacro indicado no es válido."
        reintentar={() => navegar('/saber-pro/simulacros')}
      />
    )
  }

  if (cargando) return <CargandoPresentacion />

  if (error && !presentacion) {
    return <ErrorPresentacion mensaje={error} reintentar={reintentar} onVolver={volver} />
  }

  if (!presentacion) {
    return (
      <ErrorPresentacion
        mensaje="No se pudo cargar la presentación."
        reintentar={reintentar}
        onVolver={volver}
      />
    )
  }

  if (finalizada && resultado) {
    return <VistaResultado presentacion={presentacion} resultado={resultado} onVolver={volver} />
  }

  if (!pregunta) {
    return <ErrorPresentacion mensaje="No hay una pregunta pendiente." reintentar={reintentar} />
  }

  const avance = presentacion.total_preguntas
    ? Math.round((presentacion.contenidos_respondidos / presentacion.total_preguntas) * 100)
    : 0

  return (
    <div className={cn('relative overflow-hidden rounded-2xl border', paletaSaberPro.banda, paletaSaberPro.borde)}>
      <div aria-hidden="true" className={cn('h-2 w-full', paletaSaberPro.franja)} />
      <div className="relative p-4 md:p-8">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
                {presentacion.area_nombre}
              </Badge>
              <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
                Intento {presentacion.intento}
              </Badge>
              <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
                {presentacion.curso_nombre}
              </Badge>
            </div>
            <h1 className={cn('mt-2 truncate text-xl font-bold tracking-tight md:text-2xl', paletaSaberPro.titulo)}>
              {presentacion.simulacro_titulo || 'Simulacro Saber Pro'}
            </h1>
            <p className={cn('mt-1 text-xs', paletaSaberPro.texto)}>
              Bloque {presentacion.pregunta_numero} de {presentacion.total_preguntas}
              {pregunta.parte ? ` · Parte ${pregunta.parte}` : ''}
              {pregunta.total_items > 1 ? ` · ${pregunta.total_items} ítems` : ''}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <ContadorSimulacro
              key={`${presentacion.presentacion_id}-${presentacion.contenidos_respondidos}-${presentacion.finalizada}`}
              presentacion={presentacion}
              onAgotado={() => void finalizar()}
            />
          </div>
        </header>

        <div className="mt-4">
          <div className="h-2 overflow-hidden rounded-full bg-[#1e3a5f]/10 dark:bg-[#F3EDE1]/12">
            <div
              className={cn('h-full rounded-full transition-all duration-500', paletaSaberPro.separador)}
              style={{ width: `${Math.min(100, Math.max(0, avance))}%` }}
            />
          </div>
          <p className={cn('mt-1 text-right text-[10px] uppercase tracking-[0.1em]', paletaSaberPro.apoyo)}>
            {avance}% completado
          </p>
        </div>

        {error && (
          <div className={cn('mt-4 flex items-start gap-2 rounded-xl border p-3 text-xs', 'border-[#b8432a]/30 bg-[#b8432a]/10 text-[#b8432a] dark:border-[#F29A52]/40 dark:bg-[#F29A52]/10 dark:text-[#F29A52]')}>
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <main className="mt-5 grid gap-5 xl:grid-cols-[1fr_260px]">
          <FormularioPregunta
            key={pregunta.id}
            presentacion={presentacion}
            pregunta={pregunta}
            enviando={enviando}
            onResponder={responder}
          />

          <aside className="space-y-3">
            <div className={cn('rounded-xl border p-4', paletaSaberPro.superficie, paletaSaberPro.borde)}>
              <p className={cn('text-[10px] font-semibold uppercase tracking-[0.14em]', paletaSaberPro.apoyoTitulo)}>
                Progreso
              </p>
              <div className="mt-3 space-y-2 text-xs">
                <p className={cn('flex items-center justify-between gap-2', paletaSaberPro.texto)}>
                  <span><ListChecks className="mr-1 inline h-3.5 w-3.5" /> Bloques</span>
                  <strong className={paletaSaberPro.titulo}>
                    {presentacion.contenidos_respondidos}/{presentacion.total_preguntas}
                  </strong>
                </p>
                <p className={cn('flex items-center justify-between gap-2', paletaSaberPro.texto)}>
                  <span><CheckCircle2 className="mr-1 inline h-3.5 w-3.5" /> Ítems</span>
                  <strong className={paletaSaberPro.titulo}>{presentacion.total_items}</strong>
                </p>
                <p className={cn('flex items-center justify-between gap-2', paletaSaberPro.texto)}>
                  <span><Clock className="mr-1 inline h-3.5 w-3.5" /> Límite</span>
                  <strong className={paletaSaberPro.titulo}>{presentacion.tiempo_limite_minutos} min</strong>
                </p>
              </div>
            </div>

            <div className={cn('flex items-start gap-2 rounded-xl border p-3 text-[11px]', paletaSaberPro.borde, paletaSaberPro.bandaAlterna)}>
              <ShieldCheck className={cn('mt-0.5 h-4 w-4 shrink-0', paletaSaberPro.accion)} />
              <p className={paletaSaberPro.texto}>
                Modo seguro: copiar, pegar y salir de la pestaña están restringidos durante el
                simulacro.
              </p>
            </div>

            <div className={cn('flex items-start gap-2 rounded-xl border p-3 text-[11px]', paletaSaberPro.borde, paletaSaberPro.bandaAlterna)}>
              <GraduationCap className={cn('mt-0.5 h-4 w-4 shrink-0', paletaSaberPro.accion)} />
              <p className={paletaSaberPro.texto}>
                Al agotarse el tiempo, el sistema enviará tus respuestas y finalizará el simulacro.
              </p>
            </div>
          </aside>
        </main>
      </div>
      <AvisoProteccionSimulacro
        abierto={bloqueada}
        requiereCodigo={requiereCodigo}
        codigo={codigoDesbloqueo}
        onCodigoChange={setCodigoDesbloqueo}
        onDesbloquear={() => void manejarDesbloqueo()}
        onVolver={volverAlExamen}
        desbloqueando={enviando}
        error={errorDesbloqueo}
      />
    </div>
  )
}
