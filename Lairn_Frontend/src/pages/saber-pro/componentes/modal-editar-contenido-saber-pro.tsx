// Modal de edición de una pieza del banco Saber Pro (HU-20.3).
//
// Permite al docente ajustar el contenido generado por IA antes de aprobarlo.
// Solo se abre para contenido `pendiente`: una vez aprobado, el contenido ya
// forma parte del banco de los simulacros y no se edita (lo controla el
// backend, que responde 400). La forma del formulario depende del tipo:
//
//   - Pregunta: enunciado, contexto (texto base) y opciones con su respuesta
//     correcta. La cantidad de opciones viene dada por la pieza (4, o las de la
//     parte de Inglés) y no se puede alterar.
//   - Parte 1 de Inglés (relacionar): instrucciones, las 8 palabras (A-H) y las
//     5 descripciones, cada una con la palabra que le corresponde. No hay
//     "respuesta correcta" única.
//   - Partes 2 a 7 de Inglés (bloque del examen): instrucciones, texto base
//     (obligatorio en las partes 4 a 7) y la lista de preguntas del bloque, cada
//     una con sus opciones y su respuesta correcta.
//   - Consigna: tema, contexto y enunciado.

import { useMemo, useState } from 'react'
import { useForm, Controller, useWatch } from 'react-hook-form'
import type { Resolver } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import type {
  ContenidoBancoSaberPro,
  DatosEditarContenidoSaberPro,
  RelacionContenidoSaberPro,
} from '@/types/saber-pro'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerLargo } from '../utilidades'

// Partes de Inglés cuyo bloque comparte un texto base en `contexto` (4 a 7),
// igual que el examen real. Las partes 2 y 3 son preguntas autocontenidas.
const PARTES_CON_TEXTO_COMUN_INGLES: ReadonlySet<number> = new Set([4, 5, 6, 7])

// Esquema de edición de una pregunta de selección múltiple. Revalida la misma
// forma que exige el backend: opciones no vacías y distintas, respuesta dentro
// de las opciones y texto base obligatorio en Lectura Crítica.
const esquemaEditarPregunta = (esLecturaCritica: boolean) =>
  z
    .object({
      enunciado: z.string().min(1, 'El enunciado es obligatorio'),
      opciones: z.array(z.string().min(1, 'Ninguna opción puede quedar vacía')),
      respuesta_correcta: z.string().min(1, 'Selecciona la respuesta correcta'),
      contexto: z.string().optional(),
    })
    .superRefine((val, ctx) => {
      if (val.respuesta_correcta && !val.opciones.includes(val.respuesta_correcta)) {
        ctx.addIssue({
          code: 'custom',
          path: ['respuesta_correcta'],
          message: 'La respuesta correcta debe coincidir con una opción.',
        })
      }
      if (new Set(val.opciones).size !== val.opciones.length) {
        ctx.addIssue({ code: 'custom', path: ['opciones'], message: 'Las opciones deben ser distintas entre sí.' })
      }
      if (esLecturaCritica && !val.contexto?.trim()) {
        ctx.addIssue({ code: 'custom', path: ['contexto'], message: 'El texto base es obligatorio en Lectura Crítica.' })
      }
    })

// Esquema de edición de la consigna de escritura.
const esquemaEditarConsigna = z.object({
  tema: z.string().min(1, 'El tema es obligatorio'),
  contexto: z.string().min(1, 'El contexto es obligatorio'),
  enunciado: z.string().min(1, 'La consigna es obligatoria'),
})

// Esquema de edición de la parte 1 de Inglés (tarea de relacionar): 8 palabras
// (lista A-H) y 5 descripciones, cada una emparejada con una de esas palabras.
// Aquí no existe "respuesta_correcta" única: la validación del par
// descripción-palabra replica las reglas de `relaciones` del backend.
const esquemaEditarRelacion = z
  .object({
    enunciado: z.string().min(1, 'Las instrucciones son obligatorias'),
    opciones: z.array(z.string().min(1, 'Ninguna palabra puede quedar vacía')),
    relaciones: z.array(
      z.object({
        descripcion: z.string().min(1, 'La descripción no puede quedar vacía'),
        respuesta: z.string().min(1, 'Selecciona la palabra'),
      })
    ),
    contexto: z.string().optional(),
  })
  .superRefine((val, ctx) => {
    if (val.opciones.length !== 8) {
      ctx.addIssue({ code: 'custom', path: ['opciones'], message: 'Debe haber exactamente 8 palabras (A a H).' })
    }
    if (new Set(val.opciones).size !== val.opciones.length) {
      ctx.addIssue({ code: 'custom', path: ['opciones'], message: 'Las palabras deben ser distintas entre sí.' })
    }
    const respuestas = val.relaciones.map((r) => r.respuesta).filter(Boolean)
    if (new Set(respuestas).size !== respuestas.length) {
      ctx.addIssue({ code: 'custom', path: ['relaciones'], message: 'Dos descripciones no pueden compartir la misma palabra.' })
    }
    if (respuestas.some((r) => !val.opciones.includes(r))) {
      ctx.addIssue({ code: 'custom', path: ['relaciones'], message: 'Cada respuesta debe ser una de las palabras.' })
    }
  })

// Esquema de edición de las partes 2 a 7 de Inglés (bloque completo del examen):
// instrucciones, texto base (obligatorio en las partes 4 a 7) y la lista de
// preguntas, cada una con su enunciado, sus opciones y su respuesta correcta.
// Replica las reglas del backend: sin opciones sueltas a nivel de bloque y cada
// respuesta dentro de las opciones de su propia pregunta.
const esquemaEditarBloqueIngles = (parte: number) =>
  z
    .object({
      enunciado: z.string().min(1, 'Las instrucciones del bloque son obligatorias'),
      contexto: z.string().optional(),
      preguntas: z.array(
        z.object({
          enunciado: z.string().min(1, 'La pregunta no puede quedar vacía'),
          opciones: z.array(z.string().min(1, 'Ninguna opción puede quedar vacía')),
          respuesta_correcta: z.string().min(1, 'Selecciona la respuesta correcta'),
        })
      ),
    })
    .superRefine((val, ctx) => {
      if (PARTES_CON_TEXTO_COMUN_INGLES.has(parte) && !val.contexto?.trim()) {
        ctx.addIssue({
          code: 'custom',
          path: ['contexto'],
          message: 'El texto base es obligatorio en esta parte del examen.',
        })
      }
      val.preguntas.forEach((pregunta, indice) => {
        if (pregunta.respuesta_correcta && !pregunta.opciones.includes(pregunta.respuesta_correcta)) {
          ctx.addIssue({
            code: 'custom',
            path: ['preguntas', indice, 'respuesta_correcta'],
            message: 'La respuesta correcta debe coincidir con una opción.',
          })
        }
        if (new Set(pregunta.opciones).size !== pregunta.opciones.length) {
          ctx.addIssue({
            code: 'custom',
            path: ['preguntas', indice, 'opciones'],
            message: 'Las opciones deben ser distintas entre sí.',
          })
        }
      })
    })

// Valores del formulario de edición. Agrupa los campos de todos los tipos de
// contenido; cada rama usa los suyos y deja opcionales los de las demás.
interface DatosEditarContenido {
  enunciado: string
  tema?: string
  contexto?: string
  opciones?: string[]
  respuesta_correcta?: string
  relaciones?: RelacionContenidoSaberPro[]
  preguntas?: { enunciado: string; opciones: string[]; respuesta_correcta: string }[]
}

interface ModalEditarContenidoSaberProProps {
  abierta: boolean
  contenido: ContenidoBancoSaberPro
  onCerrar: () => void
  onActualizado: () => void
}

// Extrae el mensaje de un error de react-hook-form sin importar su forma exacta
// (un error de campo expone `.message`; los errores de un array de preguntas son
// una unión de formas y basta leer ese mensaje).
const mensajeError = (error?: { message?: string }): string | undefined => error?.message

export function ModalEditarContenidoSaberPro({
  abierta,
  contenido,
  onCerrar,
  onActualizado,
}: ModalEditarContenidoSaberProProps) {
  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && onCerrar()}>
      <DialogContent className="max-h-[85vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-lg">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}>
              <Pencil className="h-5 w-5" />
            </span>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {contenido.area.nombre}
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>Editar contenido</DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Ajusta el contenido generado por IA antes de aprobarlo.
            </DialogDescription>
          </DialogHeader>
        </div>

        <FormularioEditarContenido
          key={contenido.id}
          contenido={contenido}
          onCerrar={onCerrar}
          onActualizado={onActualizado}
        />
      </DialogContent>
    </Dialog>
  )
}

function FormularioEditarContenido({
  contenido,
  onCerrar,
  onActualizado,
}: {
  contenido: ContenidoBancoSaberPro
  onCerrar: () => void
  onActualizado: () => void
}) {
  const [enviando, setEnviando] = useState(false)
  const esPregunta = contenido.tipo === 'seleccion_multiple'
  // Parte 1 de Inglés: tarea de relacionar, no es una pregunta de opción múltiple.
  const esRelacion = esPregunta && contenido.parte === 1
  // Partes 2 a 7 de Inglés: el contenido es el bloque completo del examen.
  const esBloqueIngles =
    esPregunta && contenido.parte !== null && contenido.parte !== 1 && contenido.preguntas.length > 0
  const parte = contenido.parte ?? 0
  const esLecturaCritica = contenido.area.nombre === 'Lectura Crítica'

  const esquema = useMemo(() => {
    if (esRelacion) return esquemaEditarRelacion
    if (esBloqueIngles) return esquemaEditarBloqueIngles(parte)
    return esPregunta ? esquemaEditarPregunta(esLecturaCritica) : esquemaEditarConsigna
  }, [esRelacion, esBloqueIngles, parte, esPregunta, esLecturaCritica])

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<DatosEditarContenido>({
    // El esquema es una unión (relacionar, bloque de Inglés, pregunta o
    // consigna); el tipo de valores es el común de todos, por eso se ajusta el
    // resolver.
    resolver: zodResolver(esquema) as Resolver<DatosEditarContenido>,
    defaultValues: esRelacion
      ? {
          enunciado: contenido.enunciado,
          opciones: contenido.opciones,
          relaciones: contenido.relaciones.map((r) => ({ descripcion: r.descripcion, respuesta: r.respuesta })),
          contexto: contenido.contexto,
        }
      : esBloqueIngles
        ? {
            enunciado: contenido.enunciado,
            contexto: contenido.contexto,
            preguntas: contenido.preguntas.map((p) => ({
              enunciado: p.enunciado,
              opciones: [...p.opciones],
              respuesta_correcta: p.respuesta_correcta,
            })),
          }
        : esPregunta
          ? {
              enunciado: contenido.enunciado,
              opciones: contenido.opciones,
              respuesta_correcta: contenido.respuesta_correcta,
              contexto: contenido.contexto,
            }
          : {
              tema: contenido.tema,
              contexto: contenido.contexto,
              enunciado: contenido.enunciado,
            },
  })

  // Opciones vivas para el selector de respuesta correcta (preguntas).
  const opcionesActuales = (useWatch({ control, name: 'opciones' }) as string[] | undefined) ?? []
  const opcionesVigentes = opcionesActuales.filter((o) => String(o).trim() !== '')
  // Preguntas vivas del bloque de Inglés (2 a 7) para sus selectores de respuesta.
  const preguntasActuales =
    (useWatch({ control, name: 'preguntas' }) as
      | { enunciado: string; opciones: string[]; respuesta_correcta: string }[]
      | undefined) ?? []

  const onSubmit = async (datos: DatosEditarContenido) => {
    setEnviando(true)
    try {
      const payload: DatosEditarContenidoSaberPro = esRelacion
        ? {
            enunciado: datos.enunciado,
            opciones: (datos.opciones ?? []).map((o) => o.trim()),
            relaciones: (datos.relaciones ?? []).map((r) => ({
              descripcion: r.descripcion.trim(),
              respuesta: r.respuesta,
            })),
            contexto: datos.contexto ?? '',
          }
        : esBloqueIngles
          ? {
              enunciado: datos.enunciado,
              contexto: datos.contexto ?? '',
              preguntas: (datos.preguntas ?? []).map((p) => ({
                enunciado: p.enunciado.trim(),
                opciones: p.opciones.map((o) => o.trim()),
                respuesta_correcta: p.respuesta_correcta,
              })),
            }
          : esPregunta
          ? {
              enunciado: datos.enunciado,
              opciones: (datos.opciones ?? []).map((o) => o.trim()),
              respuesta_correcta: datos.respuesta_correcta ?? '',
              contexto: datos.contexto ?? '',
            }
          : {
              tema: datos.tema ?? '',
              contexto: datos.contexto ?? '',
              enunciado: datos.enunciado,
            }

      await api.put(`/saber-pro/docente/contenido/${contenido.id}/`, payload)
      toast.success('Contenido actualizado')
      onActualizado()
      onCerrar()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo actualizar el contenido')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={`space-y-4 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
    >
      {/* Consigna: tema + contexto + enunciado */}
      {!esPregunta && (
        <>
          <div className="space-y-1.5">
            <Label htmlFor="tema" className={`${paletaSaberPro.titulo}`}>
              Tema *
            </Label>
            <Input id="tema" maxLength={200} className="bg-white dark:bg-[#243A5E]" {...register('tema')} />
            {errors.tema && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.tema.message)}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="contextoConsigna" className={`${paletaSaberPro.titulo}`}>
              Contexto *
            </Label>
            <Textarea id="contextoConsigna" rows={3} className="bg-white dark:bg-[#243A5E]" {...register('contexto')} />
            {errors.contexto && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.contexto.message)}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="enunciado" className={`${paletaSaberPro.titulo}`}>
              Consigna *
            </Label>
            <Textarea id="enunciado" rows={4} className="bg-white dark:bg-[#243A5E]" {...register('enunciado')} />
            {errors.enunciado && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.enunciado.message)}</p>}
          </div>
        </>
      )}

      {/* Parte 1 de Inglés: instrucciones, 8 palabras (A-H) y 5 descripciones */}
      {esRelacion && (
        <>
          <div className="space-y-1.5">
            <Label htmlFor="contextoRelacion" className={`${paletaSaberPro.titulo}`}>
              Contexto <span className={`text-xs font-normal ${paletaSaberPro.apoyo}`}>(opcional)</span>
            </Label>
            <Textarea id="contextoRelacion" rows={2} className="bg-white dark:bg-[#243A5E]" {...register('contexto')} />
            {errors.contexto && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.contexto.message)}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="enunciadoRelacion" className={`${paletaSaberPro.titulo}`}>
              Instrucciones *
            </Label>
            <Textarea id="enunciadoRelacion" rows={2} className="bg-white dark:bg-[#243A5E]" {...register('enunciado')} />
            {errors.enunciado && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.enunciado.message)}</p>}
          </div>

          <div className="space-y-2">
            <Label className={`${paletaSaberPro.titulo}`}>Palabras (A a H) *</Label>
            {contenido.opciones.map((_, indice) => (
              <div key={indice} className="flex items-center gap-2">
                <span className={`w-5 shrink-0 text-xs font-bold ${paletaSaberPro.apoyo}`}>
                  {String.fromCharCode(65 + indice)}.
                </span>
                <Input className="bg-white dark:bg-[#243A5E]" {...register(`opciones.${indice}`)} />
              </div>
            ))}
            {errors.opciones && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.opciones.message)}</p>}
          </div>

          <div className="space-y-3">
            <Label className={`${paletaSaberPro.titulo}`}>Descripciones *</Label>
            {contenido.relaciones.map((_, indice) => (
              <div
                key={indice}
                className={`space-y-1.5 rounded-xl border p-3 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
              >
                <Label className={`text-xs ${paletaSaberPro.apoyoTitulo}`}>Descripción {indice + 1}</Label>
                <Textarea rows={2} className="bg-white dark:bg-[#243A5E]" {...register(`relaciones.${indice}.descripcion`)} />
                <Controller
                  control={control}
                  name={`relaciones.${indice}.respuesta`}
                  render={({ field }) => (
                    <Select
                      items={opcionesVigentes.map((o) => ({ value: o, label: o }))}
                      value={(field.value as string) ?? ''}
                      onValueChange={field.onChange}
                      disabled={opcionesVigentes.length === 0}
                    >
                      {/* El popup se ensancha hasta el borde y las opciones largas
                        hacen salto de línea en vez de recortarse. */}
                      <SelectTrigger className={selectTriggerLargo}>
                        <SelectValue placeholder="Palabra que corresponde" />
                      </SelectTrigger>
                      <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                        {opcionesVigentes.map((o) => (
                          <SelectItem key={o} value={o} className={selectItemLargo}>
                            {o}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            ))}
            {errors.relaciones && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.relaciones.message)}</p>
            )}
          </div>
        </>
      )}

      {/* Partes 2 a 7 de Inglés: bloque completo del examen (instrucciones,
          texto base y cada pregunta con sus opciones respuestas). */}
      {esBloqueIngles && (
        <>
          <div className="space-y-1.5">
            <Label htmlFor="contextoBloque" className={`${paletaSaberPro.titulo}`}>
              Texto base{' '}
              {PARTES_CON_TEXTO_COMUN_INGLES.has(parte) ? (
                '*'
              ) : (
                <span className={`text-xs font-normal ${paletaSaberPro.apoyo}`}>(opcional)</span>
              )}
            </Label>
            <Textarea id="contextoBloque" rows={4} className="bg-white dark:bg-[#243A5E]" {...register('contexto')} />
            {errors.contexto && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.contexto.message)}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="enunciadoBloque" className={`${paletaSaberPro.titulo}`}>
              Instrucciones del bloque *
            </Label>
            <Textarea id="enunciadoBloque" rows={2} className="bg-white dark:bg-[#243A5E]" {...register('enunciado')} />
            {errors.enunciado && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.enunciado.message)}</p>}
          </div>

          <div className="space-y-3">
            <Label className={`${paletaSaberPro.titulo}`}>
              Preguntas del bloque ({contenido.preguntas.length}) *
            </Label>
            {contenido.preguntas.map((_, indice) => {
              const opcionesDePregunta =
                (preguntasActuales[indice]?.opciones ?? []).filter((o) => String(o).trim() !== '') ?? []
              return (
                <div
                  key={indice}
                  className={`space-y-2 rounded-xl border p-3 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
                >
                  <Label className={`text-xs ${paletaSaberPro.apoyoTitulo}`}>Pregunta {indice + 1}</Label>
                  <Textarea
                    rows={2}
                    className="bg-white dark:bg-[#243A5E]"
                    {...register(`preguntas.${indice}.enunciado`)}
                  />
                  {errors.preguntas?.[indice]?.enunciado && (
                    <p className={`text-xs ${paletaSaberPro.accion}`}>
                      {String(mensajeError(errors.preguntas?.[indice]?.enunciado as { message?: string }))}
                    </p>
                  )}

                  <div className="space-y-1.5">
                    <Label className={`text-xs ${paletaSaberPro.apoyoTitulo}`}>Opciones</Label>
                    {contenido.preguntas[indice].opciones.map((_, opcionIndice) => (
                      <div key={opcionIndice} className="flex items-center gap-2">
                        <span className={`w-5 shrink-0 text-xs font-bold ${paletaSaberPro.apoyo}`}>
                          {String.fromCharCode(65 + opcionIndice)}.
                        </span>
                        <Input
                          className="bg-white dark:bg-[#243A5E]"
                          {...register(`preguntas.${indice}.opciones.${opcionIndice}`)}
                        />
                      </div>
                    ))}
                    {errors.preguntas?.[indice]?.opciones && (
                      <p className={`text-xs ${paletaSaberPro.accion}`}>
                        {String(mensajeError(errors.preguntas?.[indice]?.opciones as { message?: string }))}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label className={`text-xs ${paletaSaberPro.apoyoTitulo}`}>Respuesta correcta</Label>
                    <Controller
                      control={control}
                      name={`preguntas.${indice}.respuesta_correcta`}
                      render={({ field }) => (
                        <Select
                          items={opcionesDePregunta.map((o) => ({ value: o, label: o }))}
                          value={(field.value as string) ?? ''}
                          onValueChange={field.onChange}
                          disabled={opcionesDePregunta.length === 0}
                        >
                          <SelectTrigger className={selectTriggerLargo}>
                            <SelectValue placeholder="Selecciona la opción correcta" />
                          </SelectTrigger>
                          <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                            {opcionesDePregunta.map((o) => (
                              <SelectItem key={o} value={o} className={selectItemLargo}>
                                {o}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {errors.preguntas?.[indice]?.respuesta_correcta && (
                      <p className={`text-xs ${paletaSaberPro.accion}`}>
                        {String(mensajeError(errors.preguntas?.[indice]?.respuesta_correcta as { message?: string }))}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Pregunta de selección múltiple: contexto (texto base), enunciado,
          opciones y respuesta correcta */}
      {esPregunta && !esRelacion && !esBloqueIngles && (
        <>
          <div className="space-y-1.5">
            <Label htmlFor="contextoPregunta" className={`${paletaSaberPro.titulo}`}>
              Contexto {esLecturaCritica ? '*' : <span className={`text-xs font-normal ${paletaSaberPro.apoyo}`}>(opcional)</span>}
            </Label>
            <Textarea id="contextoPregunta" rows={3} className="bg-white dark:bg-[#243A5E]" {...register('contexto')} />
            {errors.contexto && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.contexto.message)}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="enunciadoPregunta" className={`${paletaSaberPro.titulo}`}>
              Enunciado *
            </Label>
            <Textarea id="enunciadoPregunta" rows={3} className="bg-white dark:bg-[#243A5E]" {...register('enunciado')} />
            {errors.enunciado && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.enunciado.message)}</p>}
          </div>

          <div className="space-y-2">
            <Label className={`${paletaSaberPro.titulo}`}>Opciones *</Label>
            {contenido.opciones.map((_, indice) => (
              <Input
                key={indice}
                className="bg-white dark:bg-[#243A5E]"
                {...register(`opciones.${indice}`)}
              />
            ))}
            {errors.opciones && <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.opciones.message)}</p>}
          </div>

          <div className="space-y-1.5">
            <Label className={`${paletaSaberPro.titulo}`}>Respuesta correcta *</Label>
            <Controller
              control={control}
              name="respuesta_correcta"
              render={({ field }) => (
                <Select
                  items={opcionesVigentes.map((o) => ({ value: o, label: o }))}
                  value={(field.value as string) ?? ''}
                  onValueChange={field.onChange}
                  disabled={opcionesVigentes.length === 0}
                >
                  {/* El popup se ensancha hasta el borde y las opciones largas
                    hacen salto de línea en vez de recortarse. */}
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Selecciona la opción correcta" />
                  </SelectTrigger>
                  <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                    {opcionesVigentes.map((o) => (
                      <SelectItem key={o} value={o} className={selectItemLargo}>
                        {o}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.respuesta_correcta && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{String(errors.respuesta_correcta.message)}</p>
            )}
          </div>
        </>
      )}

      <div className={`flex justify-end gap-2 border-t pt-4 ${paletaSaberPro.borde}`}>
        <Button type="button" className={`${paletaSaberPro.botonNeutro}`} onClick={onCerrar} disabled={enviando}>
          Cancelar
        </Button>
        <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={enviando}>
          {enviando ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Pencil className="h-4 w-4" />
              Guardar cambios
            </>
          )}
        </Button>
      </div>
    </form>
  )
}