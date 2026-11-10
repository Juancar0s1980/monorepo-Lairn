// Modal para crear y editar simulacros de un curso Saber Pro (HU-19.1/19.2/19.4).
//
// El area se hereda del curso y no se edita aqui. El docente define titulo,
// descripcion, numero de preguntas (40 por defecto) y tiempo limite, y elige
// los criterios de las areas estructuradas. La estructura oficial se
// preselecciona y el reparto usa sus porcentajes: competencias en Razonamiento
// Cuantitativo/Competencias Ciudadanas y afirmaciones en Lectura Critica. En
// Ingles el examen siempre cubre las 7 partes completas, con 45 preguntas
// fijas, sin seleccion manual. El backend reparte las preguntas y selecciona el
// contenido aprobado de forma aleatoria (HU-19.3); este formulario consulta la
// disponibilidad del banco para avisar antes de guardar.

import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  AlertTriangle,
  CalendarClock,
  Check,
  ClipboardList,
  Clock,
  Layers,
  ListChecks,
  Loader2,
  Repeat,
  Sparkles,
  Type,
  Wand2,
} from 'lucide-react'
import { toast } from 'sonner'
import type { CursoSaberPro, SimulacroSaberPro } from '@/types/saber-pro'
import { useDisponibilidadSimulacroSaberPro } from '@/hooks/use-disponibilidad-simulacro-saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

const esquemaSimulacro = z.object({
  titulo: z.string().max(150, 'Maximo 150 caracteres').optional(),
  descripcion: z.string().max(1000, 'Maximo 1000 caracteres').optional(),
  num_preguntas: z.coerce.number().int().min(1, 'Minimo 1 pregunta').max(200, 'Maximo 200 preguntas'),
  tiempo_limite_minutos: z.coerce.number().int().min(1, 'Minimo 1 minuto').max(600, 'Maximo 600 minutos'),
  intentos_maximos: z.coerce
    .number()
    .int()
    .min(1, 'Minimo 1 intento')
    .max(100, 'Maximo 100 intentos'),
  fecha_limite: z.string().optional(),
  limite_palabras: z
    .string()
    .optional()
    .refine(
      (valor) =>
        !valor ||
        (Number.isInteger(Number(valor)) && Number(valor) >= 1 && Number(valor) <= 10000),
      'Usa un entero entre 1 y 10000'
    ),
})

type EntradaFormularioSimulacro = z.input<typeof esquemaSimulacro>
type DatosFormularioSimulacro = z.output<typeof esquemaSimulacro>

interface ModalSimulacroSaberProProps {
  abierta: boolean
  curso: CursoSaberPro
  simulacro?: SimulacroSaberPro | null
  onCerrar: () => void
  onGuardado: () => void
}

function distribuirPorPesos(total: number, pesos: number[]): number[] {
  if (pesos.length === 0) return []
  if (total < pesos.length) return pesos.map(() => 0)

  const pesosValidos = pesos.map((peso) => Math.max(0, peso))
  let suma = pesosValidos.reduce((acumulado, peso) => acumulado + peso, 0)
  if (suma <= 0) {
    pesosValidos.fill(1)
    suma = pesosValidos.length
  }

  const exactos = pesosValidos.map((peso) => (total * peso) / suma)
  const cantidades = exactos.map(Math.floor)
  const restante = total - cantidades.reduce((acumulado, cantidad) => acumulado + cantidad, 0)
  const orden = exactos
    .map((exacto, indice) => ({ indice, residuo: exacto - cantidades[indice] }))
    .sort((a, b) => b.residuo - a.residuo || a.indice - b.indice)
  for (const { indice } of orden.slice(0, restante)) cantidades[indice] += 1

  for (let indice = 0; indice < cantidades.length; indice += 1) {
    if (cantidades[indice] > 0) continue
    const donante = cantidades.reduce(
      (mejor, cantidad, posicion) => (cantidad > cantidades[mejor] ? posicion : mejor),
      0
    )
    if (cantidades[donante] > 1) {
      cantidades[donante] -= 1
      cantidades[indice] += 1
    }
  }
  return cantidades
}

function claveDeDistribucion(distribucion: SimulacroSaberPro['distribuciones'][number]): string {
  if (distribucion.afirmacion) return `afirmacion:${distribucion.afirmacion.id}`
  if (distribucion.competencia) return `competencia:${distribucion.competencia.id}`
  return `parte:${distribucion.parte}`
}

function aDatetimeLocal(valor?: string | null): string {
  if (!valor) return ''
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''
  const local = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function aIso(valor?: string): string | null {
  if (!valor) return null
  const fecha = new Date(valor)
  return Number.isNaN(fecha.getTime()) ? null : fecha.toISOString()
}

function mensajeDeError(error: unknown): string {
  const axiosError = error as {
    response?: { data?: { detalle?: string; errores?: string[] } & Record<string, unknown> }
  }
  const datos = axiosError.response?.data
  if (!datos) return 'No se pudo guardar el simulacro.'
  const mensajes: string[] = []
  if (datos.detalle) mensajes.push(datos.detalle)
  if (Array.isArray(datos.errores)) mensajes.push(...datos.errores)
  for (const [campo, valor] of Object.entries(datos)) {
    if (campo === 'detalle' || campo === 'errores') continue
    if (Array.isArray(valor)) mensajes.push(...valor.map(String))
    else if (typeof valor === 'string') mensajes.push(valor)
  }
  return mensajes.length ? mensajes.join(' ') : 'No se pudo guardar el simulacro.'
}

export function ModalSimulacroSaberPro({
  abierta,
  curso,
  simulacro,
  onCerrar,
  onGuardado,
}: ModalSimulacroSaberProProps) {
  const [enviando, setEnviando] = useState(false)
  const [seleccion, setSeleccion] = useState<Set<string>>(new Set())
  const editando = Boolean(simulacro)

  const { disponibilidad, cargando: cargandoDisponibilidad, error: errorDisponibilidad } =
    useDisponibilidadSimulacroSaberPro(curso.id, abierta)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<EntradaFormularioSimulacro, unknown, DatosFormularioSimulacro>({
    resolver: zodResolver(esquemaSimulacro),
    defaultValues: {
      titulo: '',
      descripcion: '',
      num_preguntas: curso.area.nombre === 'Comunicación Escrita' ? 1 : 40,
      tiempo_limite_minutos: 60,
      intentos_maximos: 1,
      fecha_limite: '',
      limite_palabras: '',
    },
  })

  const estructura = disponibilidad?.tipo_estructura
  const esIngles = curso.area.nombre === 'Inglés' || estructura === 'partes'
  const esLecturaCritica = curso.area.nombre === 'Lectura Crítica'
  const esConsigna = curso.area.nombre === 'Comunicación Escrita' || estructura === 'consigna'
  const totalPreguntasIngles =
    disponibilidad?.partes.reduce((total, parte) => total + parte.preguntas, 0) || 45
  const numPreguntas = esIngles
    ? totalPreguntasIngles
    : Number(watch('num_preguntas')) || (esConsigna ? 1 : 40)

  useEffect(() => {
    if (!abierta) return
    reset({
      titulo: simulacro?.titulo ?? '',
      descripcion: simulacro?.descripcion ?? '',
      num_preguntas: esIngles
        ? totalPreguntasIngles
        : esConsigna
          ? simulacro?.num_preguntas ?? 1
          : simulacro?.num_preguntas ?? 40,
      tiempo_limite_minutos: simulacro?.tiempo_limite_minutos ?? 60,
      intentos_maximos: simulacro?.intentos_maximos ?? 1,
      fecha_limite: aDatetimeLocal(simulacro?.fecha_limite),
      limite_palabras: simulacro?.limite_palabras ? String(simulacro.limite_palabras) : '',
    })
    const guardadas = simulacro?.distribuciones.map(claveDeDistribucion) ?? []
    const oficiales =
      disponibilidad?.tipo_estructura === 'competencias'
        ? disponibilidad.competencias.flatMap((competencia) =>
            esLecturaCritica
              ? competencia.afirmaciones.map((afirmacion) => `afirmacion:${afirmacion.id}`)
              : [`competencia:${competencia.id}`]
          )
        : []
    setSeleccion(new Set(guardadas.length > 0 ? guardadas : oficiales))
  }, [abierta, disponibilidad, esConsigna, esIngles, esLecturaCritica, reset, simulacro, totalPreguntasIngles])

  const criteriosDisponibles = useMemo(() => {
    if (!disponibilidad) {
      return new Map<string, { nombre: string; peso: number; disponibles: number }>()
    }
    const mapa = new Map<string, { nombre: string; peso: number; disponibles: number }>()
    for (const competencia of disponibilidad.competencias) {
      mapa.set(`competencia:${competencia.id}`, {
        nombre: competencia.nombre,
        peso: competencia.peso,
        disponibles: competencia.disponibles,
      })
      for (const afirmacion of competencia.afirmaciones) {
        mapa.set(`afirmacion:${afirmacion.id}`, {
          nombre: afirmacion.nombre,
          peso: afirmacion.peso,
          disponibles: afirmacion.disponibles,
        })
      }
    }
    for (const parte of disponibilidad.partes) {
      mapa.set(`parte:${parte.numero}`, {
        nombre: `Parte ${parte.numero}`,
        peso: parte.peso,
        disponibles: parte.disponibles,
      })
    }
    return mapa
  }, [disponibilidad])

  const criteriosOficiales = useMemo(() => {
    if (disponibilidad?.tipo_estructura !== 'competencias') return []
    return disponibilidad.competencias.flatMap((competencia) =>
      esLecturaCritica
        ? competencia.afirmaciones.map((afirmacion) => `afirmacion:${afirmacion.id}`)
        : [`competencia:${competencia.id}`]
    )
  }, [disponibilidad, esLecturaCritica])

  const criteriosSeleccionados = useMemo(() => Array.from(seleccion), [seleccion])
  const clavesDistribucion =
    criteriosSeleccionados.length > 0 ? criteriosSeleccionados : criteriosOficiales

  const cantidades = useMemo(() => {
    const pesos = clavesDistribucion.map((clave) => criteriosDisponibles.get(clave)?.peso ?? 0)
    return distribuirPorPesos(numPreguntas, pesos)
  }, [clavesDistribucion, criteriosDisponibles, numPreguntas])

  const resumenDistribucion = useMemo(() => {
    return clavesDistribucion.map((clave, indice) => ({
      clave,
      nombre: criteriosDisponibles.get(clave)?.nombre ?? 'Criterio no disponible',
      peso: criteriosDisponibles.get(clave)?.peso ?? 0,
      disponibles: criteriosDisponibles.get(clave)?.disponibles ?? 0,
      cantidad: cantidades[indice] ?? 0,
    }))
  }, [cantidades, clavesDistribucion, criteriosDisponibles])

  const totalAprobados = disponibilidad?.total_aprobados ?? 0

  const advertencias = useMemo(() => {
    const mensajes: string[] = []
    if (!disponibilidad) return mensajes
    if (esIngles) {
      const faltantes = disponibilidad.partes.filter((parte) => parte.disponibles === 0)
      if (faltantes.length > 0) {
        mensajes.push(
          `Faltan bloques aprobados para: ${faltantes
            .map((parte) => `Parte ${parte.numero}`)
            .join(', ')}. El examen de Inglés debe cubrir las 7 partes.`
        )
      }
      return mensajes
    }
    if (clavesDistribucion.length > numPreguntas) {
      mensajes.push('El numero de preguntas debe ser al menos igual a la cantidad de criterios seleccionados.')
    }
    if (estructura === 'consigna' && totalAprobados < numPreguntas) {
      mensajes.push(
        `El banco del area solo tiene ${totalAprobados} contenidos aprobados y el simulacro requiere ${numPreguntas}.`
      )
    }
    for (const item of resumenDistribucion) {
      if (item.cantidad > item.disponibles) {
        mensajes.push(`"${item.nombre}" solo tiene ${item.disponibles} contenidos aprobados y se le asignarian ${item.cantidad}.`)
      }
    }
    return mensajes
  }, [clavesDistribucion.length, disponibilidad, esIngles, estructura, numPreguntas, resumenDistribucion, totalAprobados])

  const faltanPartesIngles =
    esIngles && Boolean(disponibilidad?.partes.some((parte) => parte.disponibles === 0))
  const bloqueado =
    enviando ||
    Boolean(errorDisponibilidad) ||
    (disponibilidad !== null && (esIngles ? faltanPartesIngles : totalAprobados === 0))

  const alternarCriterio = (clave: string) => {
    setSeleccion((anterior) => {
      const siguiente = new Set(anterior)
      if (siguiente.has(clave)) siguiente.delete(clave)
      else siguiente.add(clave)
      return siguiente
    })
  }

  const onSubmit = async (datos: DatosFormularioSimulacro) => {
    setEnviando(true)
    try {
      const distribuciones = criteriosSeleccionados.map((clave) => {
        const [tipo, valor] = clave.split(':')
        if (tipo === 'competencia') return { competencia_id: Number(valor) }
        if (tipo === 'afirmacion') return { afirmacion_id: Number(valor) }
        return { parte: Number(valor) }
      })
      const payload = {
        titulo: datos.titulo?.trim() || '',
        descripcion: datos.descripcion?.trim() || '',
        num_preguntas: esIngles ? totalPreguntasIngles : datos.num_preguntas,
        tiempo_limite_minutos: datos.tiempo_limite_minutos,
        intentos_maximos: datos.intentos_maximos,
        fecha_limite: aIso(datos.fecha_limite),
        limite_palabras:
          esConsigna && datos.limite_palabras ? Number(datos.limite_palabras) : null,
        ...(esIngles ? {} : { distribuciones }),
      }
      if (simulacro) {
        await api.patch(`/saber-pro/docente/cursos/${curso.id}/simulacros/${simulacro.id}/`, payload)
        toast.success('Simulacro actualizado')
      } else {
        await api.post(`/saber-pro/docente/cursos/${curso.id}/simulacros/`, payload)
        toast.success('Simulacro creado y preguntas asignadas')
      }
      onGuardado()
      onCerrar()
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && !enviando && onCerrar()}>
      <DialogContent className="max-h-[90vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-2xl">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}>
              <ClipboardList className="h-6 w-6" />
            </span>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {curso.area.nombre} · {curso.nombre}
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>
              {editando ? 'Editar simulacro' : 'Nuevo simulacro'}
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              El area se hereda del curso. Define la evaluacion y el sistema seleccionara contenido aprobado de tu banco.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className={`space-y-5 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="titulo-simulacro" className={paletaSaberPro.titulo}>
                Titulo
              </Label>
              <Input
                id="titulo-simulacro"
                placeholder={`Simulacro de ${curso.area.nombre}`}
                maxLength={150}
                className="bg-white dark:bg-[#243A5E]"
                {...register('titulo')}
              />
              {errors.titulo && <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.titulo.message}</p>}
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="descripcion-simulacro" className={paletaSaberPro.titulo}>
                Descripcion
              </Label>
              <Textarea
                id="descripcion-simulacro"
                placeholder="Proposito pedagogico del simulacro"
                rows={2}
                maxLength={1000}
                className="bg-white dark:bg-[#243A5E]"
                {...register('descripcion')}
              />
            </div>

            {esIngles ? (
              <div className="space-y-1.5">
                <Label className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                  <ListChecks className="h-3.5 w-3.5" /> Numero de preguntas
                </Label>
                <div
                  className={cn(
                    'flex h-9 items-center rounded-md border px-3 text-sm font-semibold',
                    'border-[rgba(30,58,95,0.18)] bg-[#f3ede1]/70 text-[#1e3a5f]',
                    'dark:border-[rgba(243,237,225,0.28)] dark:bg-[#172A45]/70 dark:text-[#F5EFE0]'
                  )}
                >
                  {totalPreguntasIngles} preguntas fijas
                </div>
                <p className={`text-[10px] leading-relaxed ${paletaSaberPro.apoyo}`}>
                  El examen cubre las 7 partes completas.
                </p>
                <input type="hidden" {...register('num_preguntas')} />
              </div>
            ) : (
              <div className="space-y-1.5">
                <Label htmlFor="num-preguntas" className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                  <ListChecks className="h-3.5 w-3.5" />{' '}
                  {esConsigna ? 'Número de consignas' : 'Número de preguntas'}
                </Label>
                <Input
                  id="num-preguntas"
                  type="number"
                  min={1}
                  max={200}
                  className="bg-white dark:bg-[#243A5E]"
                  {...register('num_preguntas')}
                />
                {errors.num_preguntas && (
                  <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.num_preguntas.message}</p>
                )}
                {esConsigna && (
                  <p className={`text-[10px] leading-relaxed ${paletaSaberPro.apoyo}`}>
                    Por defecto se asigna 1 consigna de escritura, como en el examen real. Puedes
                    ajustar la cantidad si tu práctica lo requiere.
                  </p>
                )}
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="tiempo-simulacro" className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                <Clock className="h-3.5 w-3.5" /> Tiempo limite (minutos)
              </Label>
              <Input
                id="tiempo-simulacro"
                type="number"
                min={1}
                max={600}
                className="bg-white dark:bg-[#243A5E]"
                {...register('tiempo_limite_minutos')}
              />
              {errors.tiempo_limite_minutos && (
                <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.tiempo_limite_minutos.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="fecha-limite-simulacro" className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                <CalendarClock className="h-3.5 w-3.5" /> Fecha limite (opcional)
              </Label>
              <Input
                id="fecha-limite-simulacro"
                type="datetime-local"
                className="bg-white dark:bg-[#243A5E]"
                {...register('fecha_limite')}
              />
              <p className={`text-[10px] leading-relaxed ${paletaSaberPro.apoyo}`}>
                Despues de esta fecha no se podran iniciar intentos nuevos. Un intento en curso se
                cierra automaticamente al cumplirse el plazo.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="intentos-simulacro" className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                <Repeat className="h-3.5 w-3.5" /> Intentos maximos por estudiante
              </Label>
              <Input
                id="intentos-simulacro"
                type="number"
                min={1}
                max={100}
                className="bg-white dark:bg-[#243A5E]"
                {...register('intentos_maximos')}
              />
              {errors.intentos_maximos && (
                <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.intentos_maximos.message}</p>
              )}
              <p className={`text-[10px] leading-relaxed ${paletaSaberPro.apoyo}`}>
                Al agotar este limite el estudiante no podra iniciar un intento nuevo.
              </p>
            </div>

            {esConsigna && (
              <div className="space-y-1.5">
                <Label htmlFor="limite-palabras-simulacro" className={`flex items-center gap-1.5 ${paletaSaberPro.titulo}`}>
                  <Type className="h-3.5 w-3.5" /> Limite de palabras por consigna
                </Label>
                <Input
                  id="limite-palabras-simulacro"
                  type="number"
                  min={1}
                  max={10000}
                  placeholder="Sin limite"
                  className="bg-white dark:bg-[#243A5E]"
                  {...register('limite_palabras')}
                />
                {errors.limite_palabras && (
                  <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.limite_palabras.message}</p>
                )}
                <p className={`text-[10px] leading-relaxed ${paletaSaberPro.apoyo}`}>
                  Vacio significa sin limite. El estudiante vera el contador mientras escribe.
                </p>
              </div>
            )}
          </div>

          <div className={`rounded-xl border p-4 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}>
            <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className={`flex items-center gap-1.5 text-sm font-semibold ${paletaSaberPro.titulo}`}>
                  <Layers className="h-4 w-4" />{' '}
                  {esIngles ? 'Estructura fija del examen' : 'Criterios a cubrir'}
                </p>
                <p className={`mt-0.5 text-xs ${paletaSaberPro.apoyo}`}>
                  {esIngles
                    ? 'Inglés siempre incluye las 7 partes con la cantidad oficial de preguntas de cada una.'
                    : 'La estructura oficial se preselecciona y el reparto respeta sus porcentajes. Puedes ajustar los criterios.'}
                </p>
              </div>
              <Badge variant="outline" className={cn('w-fit gap-1 text-[10px]', paletaSaberPro.badge)}>
                <Sparkles className="h-3 w-3" /> {totalAprobados}{' '}
                {esIngles ? 'bloques aprobados' : 'aprobados'}
              </Badge>
            </div>

            {cargandoDisponibilidad && (
              <p className={`mt-4 flex items-center gap-2 text-xs ${paletaSaberPro.apoyo}`}>
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Consultando banco aprobado...
              </p>
            )}

            {errorDisponibilidad && (
              <p className={`mt-4 flex items-center gap-2 text-xs ${paletaSaberPro.accion}`}>
                <AlertTriangle className="h-3.5 w-3.5" /> {errorDisponibilidad}
              </p>
            )}

            {disponibilidad && estructura === 'competencias' && (
              <div className="mt-4 space-y-3">
                {disponibilidad.competencias.map((competencia) =>
                  esLecturaCritica ? (
                    <div key={competencia.id} className="space-y-1.5">
                      <p className={cn('px-1 text-[11px] font-semibold', paletaSaberPro.texto)}>
                        {competencia.nombre}
                      </p>
                      <div className={`ml-3 space-y-1.5 border-l pl-3 ${paletaSaberPro.borde}`}>
                        {competencia.afirmaciones.map((afirmacion) => (
                          <BotonCriterio
                            key={afirmacion.id}
                            activo={seleccion.has(`afirmacion:${afirmacion.id}`)}
                            peso={afirmacion.peso}
                            disponibles={afirmacion.disponibles}
                            onClick={() => alternarCriterio(`afirmacion:${afirmacion.id}`)}
                            pequeno
                          >
                            {afirmacion.nombre}
                          </BotonCriterio>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <BotonCriterio
                      key={competencia.id}
                      activo={seleccion.has(`competencia:${competencia.id}`)}
                      peso={competencia.peso}
                      disponibles={competencia.disponibles}
                      onClick={() => alternarCriterio(`competencia:${competencia.id}`)}
                    >
                      {competencia.nombre}
                    </BotonCriterio>
                  )
                )}
                <p className={cn('text-[10px] leading-relaxed', paletaSaberPro.apoyo)}>
                  {esLecturaCritica
                    ? 'Los porcentajes oficiales se reparten entre las afirmaciones.'
                    : 'Los porcentajes oficiales se reparten entre las competencias.'}
                </p>
              </div>
            )}

            {disponibilidad && estructura === 'partes' && (
              <div className="mt-4 space-y-1.5">
                {disponibilidad.partes.map((parte) => {
                  const disponible = parte.disponibles > 0
                  return (
                    <div
                      key={parte.numero}
                      className={cn(
                        'flex items-start justify-between gap-3 rounded-lg border px-3 py-2',
                        disponible
                          ? 'border-[rgba(30,58,95,0.12)] dark:border-[rgba(243,237,225,0.18)]'
                          : 'border-[#e8740e]/40 bg-[#e8740e]/5 dark:border-[#F29A52]/50 dark:bg-[#F29A52]/10'
                      )}
                    >
                      <span className="flex min-w-0 items-start gap-2">
                        <span
                          className={cn(
                            'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold',
                            paletaSaberPro.numeracionPaso
                          )}
                        >
                          {parte.numero}
                        </span>
                        <span className="min-w-0">
                          <span className={cn('block text-xs font-semibold', paletaSaberPro.texto)}>
                            {parte.nombre}
                          </span>
                          <span className={cn('block text-[10px]', paletaSaberPro.apoyo)}>
                            {parte.preguntas} preguntas · {parte.peso}% del examen
                          </span>
                        </span>
                      </span>
                      <span
                        className={cn(
                          'shrink-0 text-right text-[10px] font-medium',
                          disponible ? paletaSaberPro.apoyo : paletaSaberPro.accion
                        )}
                      >
                        {disponible
                          ? `${parte.disponibles} bloque${parte.disponibles === 1 ? '' : 's'}`
                          : 'Falta bloque'}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}

            {disponibilidad && estructura === 'consigna' && (
              <p className={`mt-4 text-xs leading-relaxed ${paletaSaberPro.texto}`}>
                Comunicación Escrita no usa competencias ni partes: se seleccionarán{' '}
                {numPreguntas === 1 ? '1 consigna aprobada' : `${numPreguntas} consignas aprobadas`} del
                banco del área de forma aleatoria.
              </p>
            )}
          </div>

          <div className={`rounded-xl border p-4 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}>
            <p className={`flex items-center gap-1.5 text-sm font-semibold ${paletaSaberPro.titulo}`}>
              <Wand2 className="h-4 w-4" />{' '}
              {esIngles
                ? 'Composición fija del examen'
                : esConsigna
                  ? 'Asignación de consignas'
                  : 'Distribución automática'}
            </p>
            {esIngles ? (
              <>
                <p className={`mt-1 text-xs ${paletaSaberPro.texto}`}>
                  Se asignara un bloque aprobado por cada parte, con {totalPreguntasIngles} preguntas en
                  total. La cantidad no se puede reducir ni ampliar.
                </p>
                {disponibilidad && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {disponibilidad.partes.map((parte) => (
                      <span
                        key={parte.numero}
                        className={cn(
                          'rounded-full border px-2.5 py-1 text-[11px]',
                          parte.disponibles > 0
                            ? paletaSaberPro.badge
                            : 'border-[#e8740e]/50 text-[#e8740e] dark:border-[#F29A52]/60 dark:text-[#F29A52]'
                        )}
                      >
                        Parte {parte.numero}: {parte.preguntas}
                      </span>
                    ))}
                  </div>
                )}
              </>
            ) : esConsigna ? (
              <p className={`mt-1 text-xs ${paletaSaberPro.texto}`}>
                Se {numPreguntas === 1 ? 'asignará 1 consigna aprobada' : `asignarán ${numPreguntas} consignas aprobadas`}{' '}
                del banco del área de forma aleatoria.
              </p>
            ) : clavesDistribucion.length === 0 ? (
              <p className={`mt-1 text-xs ${paletaSaberPro.texto}`}>
                Se asignarán {numPreguntas} contenidos aleatorios de todo el banco aprobado.
              </p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {resumenDistribucion.map((item) => (
                  <span
                    key={item.clave}
                    className={cn(
                      'rounded-full border px-2.5 py-1 text-[11px]',
                      item.cantidad > item.disponibles
                        ? 'border-[#e8740e]/50 text-[#e8740e] dark:border-[#F29A52]/60 dark:text-[#F29A52]'
                        : paletaSaberPro.badge
                    )}
                  >
                    {item.nombre}: {item.cantidad} ({item.peso}%)
                  </span>
                ))}
              </div>
            )}
          </div>

          {advertencias.length > 0 && (
            <div className="space-y-1 rounded-xl border border-[#e8740e]/40 bg-[#e8740e]/5 p-3 dark:border-[#F29A52]/50 dark:bg-[#F29A52]/10">
              {advertencias.map((advertencia) => (
                <p key={advertencia} className={`flex gap-1.5 text-xs ${paletaSaberPro.accion}`}>
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {advertencia}
                </p>
              ))}
            </div>
          )}

          <div className={`flex flex-col-reverse gap-2 border-t pt-4 sm:flex-row sm:justify-end ${paletaSaberPro.borde}`}>
            <Button
              type="button"
              className={paletaSaberPro.botonNeutro}
              onClick={onCerrar}
              disabled={enviando}
            >
              Cancelar
            </Button>
            <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={bloqueado}>
              {enviando ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Guardando...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4" /> {editando ? 'Guardar cambios' : 'Crear simulacro'}
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

interface BotonCriterioProps {
  activo: boolean
  peso: number
  disponibles: number
  onClick: () => void
  children: ReactNode
  pequeno?: boolean
}

function BotonCriterio({ activo, peso, disponibles, onClick, children, pequeno }: BotonCriterioProps) {
  const deshabilitado = disponibles === 0
  return (
    <button
      type="button"
      aria-pressed={activo}
      onClick={onClick}
      disabled={deshabilitado}
      className={cn(
        'flex w-full items-start justify-between gap-2 rounded-lg border text-left transition-colors',
        pequeno ? 'px-2.5 py-1.5 text-[11px]' : 'px-3 py-2 text-xs',
        activo
          ? 'border-[#1e3a5f] bg-[#1e3a5f]/5 dark:border-[#E3C063] dark:bg-[#E3C063]/10'
          : 'border-[rgba(30,58,95,0.12)] bg-transparent dark:border-[rgba(243,237,225,0.18)]',
        deshabilitado
          ? 'cursor-not-allowed opacity-45'
          : 'hover:border-[#c89b14]/60 hover:bg-[#c89b14]/5 dark:hover:border-[#E3C063]/60'
      )}
    >
      <span className="flex min-w-0 items-start gap-2">
        <span
          className={cn(
            'mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border',
            activo
              ? 'border-[#1e3a5f] bg-[#1e3a5f] text-white dark:border-[#E3C063] dark:bg-[#E3C063] dark:text-[#172A45]'
              : 'border-[rgba(30,58,95,0.35)] dark:border-[rgba(243,237,225,0.4)]'
          )}
        >
          {activo && <Check className="h-2.5 w-2.5" />}
        </span>
        <span className={paletaSaberPro.texto}>{children}</span>
      </span>
      <span className={cn('shrink-0 text-[10px]', paletaSaberPro.apoyo)}>
        {disponibles} · {peso}%
      </span>
    </button>
  )
}
