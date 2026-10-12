// Modal de generación de contenido del banco Saber Pro con IA (HU-20.1/20.2).
//
// El formulario se adapta a la estructura del área del curso (HU-20.1):
//
//   - Áreas estructuradas: cascada competencia → afirmación → evidencia
//     (la evidencia es opcional porque el catálogo oficial tiene afirmaciones
//     sin evidencias definidas).
//   - Inglés: selector de la parte del examen (1 a 7), que define la tarea y
//     la cantidad de opciones.
//   - Comunicación Escrita: sin criterios; se generan consignas de escritura.
//
// El formulario no arma prompts: solo envía los criterios elegidos (y la
// cantidad en las áreas que admiten varias piezas) a `POST .../contenido/generar/`.
// En Inglés no se envía `cantidad`: cada parte se genera como la parte COMPLETA
// del examen (un solo bloque con todas sus preguntas); el backend valida contra
// la estructura del área y persiste el contenido como `pendiente`. La respuesta
// es la lista de piezas generadas.

import { useMemo, useState } from 'react'
import { useForm, Controller, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import type {
  ContenidoBancoSaberPro,
  CriteriosAreaSaberPro,
  CursoSaberPro,
  DatosGenerarContenidoSaberPro,
  ParteInglesSaberPro,
} from '@/types/saber-pro'
import { useCriteriosAreaSaberPro } from '@/hooks/use-criterios-area-saber-pro'
import {
  paletaSaberPro,
  selectContenidoAncho,
  selectItemLargo,
  selectTriggerAncho,
  selectTriggerLargo,
} from '../utilidades'

// Valor centinela para "sin evidencia específica" en el selector de evidencia.
const SIN_EVIDENCIA = 'ninguna'

// Forma de una parte de Inglés para el selector: cada parte se genera como un
// bloque completo del examen. La parte 1 es de relacionar (8 palabras para 5
// descripciones); el resto son bloques con sus preguntas de opción múltiple.
const formaDeParte = (p: ParteInglesSaberPro) =>
  p.numero === 1
    ? `bloque · ${p.descripciones} descripciones / ${p.opciones} palabras`
    : `bloque · ${p.preguntas} preguntas de ${p.opciones} opciones`

// Esquema de validación de la generación. La estructura del área decide qué
// campos son obligatorios: competencia/afirmación en áreas estructuradas y
// parte en Inglés; la cantidad solo aplica fuera de Inglés (allí la parte
// completa se genera en un solo bloque, sin cantidad).
const esquemaGenerarContenido = (tipo: CriteriosAreaSaberPro['tipo_estructura']) =>
  z
    .object({
      competencia_id: z.string().optional(),
      afirmacion_id: z.string().optional(),
      evidencia_id: z.string().optional(),
      parte: z.string().optional(),
      cantidad: z.string().optional(),
    })
    .superRefine((val, ctx) => {
      if (tipo === 'competencias') {
        if (!val.competencia_id) {
          ctx.addIssue({ code: 'custom', path: ['competencia_id'], message: 'Selecciona una competencia.' })
        }
        if (!val.afirmacion_id) {
          ctx.addIssue({ code: 'custom', path: ['afirmacion_id'], message: 'Selecciona una afirmación.' })
        }
        if (!val.cantidad) {
          ctx.addIssue({ code: 'custom', path: ['cantidad'], message: 'Selecciona la cantidad.' })
        }
      }
      if (tipo === 'partes' && !val.parte) {
        ctx.addIssue({ code: 'custom', path: ['parte'], message: 'Selecciona la parte del examen.' })
      }
      if (tipo === 'consigna' && !val.cantidad) {
        ctx.addIssue({ code: 'custom', path: ['cantidad'], message: 'Selecciona la cantidad.' })
      }
    })

type DatosGenerarContenido = z.infer<ReturnType<typeof esquemaGenerarContenido>>

interface ModalGenerarContenidoSaberProProps {
  abierta: boolean
  curso: CursoSaberPro
  onCerrar: () => void
  /** Se invoca tras generar contenido nuevo para refrescar el banco. */
  onGenerado: () => void
}

export function ModalGenerarContenidoSaberPro({
  abierta,
  curso,
  onCerrar,
  onGenerado,
}: ModalGenerarContenidoSaberProProps) {
  // Solo carga los criterios cuando el modal está abierto, para el área del curso.
  const { criterios, cargando, error } = useCriteriosAreaSaberPro(abierta ? curso.area.id : null)

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && onCerrar()}>
      <DialogContent className="max-h-[85vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-lg">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}>
              <Sparkles className="h-6 w-6" />
            </span>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {curso.area.nombre}
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>Generar contenido con IA</DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Elige los criterios y la IA redactará el contenido. Quedará pendiente
              hasta que lo revises y lo apruebes.
            </DialogDescription>
          </DialogHeader>
        </div>

        {cargando && (
          <div className={`flex items-center justify-center gap-2 border-t p-10 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
            <Loader2 className={`h-5 w-5 animate-spin ${paletaSaberPro.accion}`} />
            <span className={`text-sm ${paletaSaberPro.apoyo}`}>Cargando criterios del área...</span>
          </div>
        )}

        {!cargando && error && (
          <div className={`border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
            <p className={`text-sm ${paletaSaberPro.accion}`}>{error}</p>
          </div>
        )}

        {!cargando && !error && criterios && (
          <FormularioGenerarContenido
            key={curso.id}
            curso={curso}
            criterios={criterios}
            onCerrar={onCerrar}
            onGenerado={onGenerado}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

// Formulario interno: se monta solo cuando los criterios están disponibles, de
// modo que la estructura del área (y su esquema de validación) sean estables.
function FormularioGenerarContenido({
  curso,
  criterios,
  onCerrar,
  onGenerado,
}: {
  curso: CursoSaberPro
  criterios: CriteriosAreaSaberPro
  onCerrar: () => void
  onGenerado: () => void
}) {
  const [enviando, setEnviando] = useState(false)
  const tipo = criterios.tipo_estructura
  const esquema = useMemo(() => esquemaGenerarContenido(tipo), [tipo])

  const {
    control,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<DatosGenerarContenido>({
    resolver: zodResolver(esquema),
    defaultValues: {
      competencia_id: '',
      afirmacion_id: '',
      evidencia_id: SIN_EVIDENCIA,
      parte: '',
      cantidad: '3',
    },
  })

  // useWatch (no watch) para leer los campos en render sin romper la
  // memoización del React Compiler.
  const competenciaId = useWatch({ control, name: 'competencia_id' })
  const afirmacionId = useWatch({ control, name: 'afirmacion_id' })

  // Derivados de la cascada: afirmaciones de la competencia elegida y sus
  // evidencias. Se recalculan al cambiar la selección padre.
  const afirmacionesDeCompetencia = useMemo(
    () => criterios.competencias.find((c) => String(c.id) === competenciaId)?.afirmaciones ?? [],
    [criterios.competencias, competenciaId]
  )

  const evidenciasDeAfirmacion = useMemo(() => {
    for (const competencia of criterios.competencias) {
      const afirmacion = competencia.afirmaciones.find((a) => String(a.id) === afirmacionId)
      if (afirmacion) return afirmacion.evidencias
    }
    return []
  }, [criterios.competencias, afirmacionId])

  const onSubmit = async (datos: DatosGenerarContenido) => {
    setEnviando(true)
    try {
      const payload: DatosGenerarContenidoSaberPro = {}
      if (tipo === 'competencias') {
        payload.competencia_id = Number(datos.competencia_id)
        payload.afirmacion_id = Number(datos.afirmacion_id)
        if (datos.evidencia_id && datos.evidencia_id !== SIN_EVIDENCIA) {
          payload.evidencia_id = Number(datos.evidencia_id)
        }
        payload.cantidad = Number(datos.cantidad)
      } else if (tipo === 'partes') {
        // Sin `cantidad`: la parte completa del examen se genera en un solo bloque.
        payload.parte = Number(datos.parte)
      } else {
        payload.cantidad = Number(datos.cantidad)
      }

      // La generación con IA es lenta de forma variable (el modelo razona y el
      // SDK reintenta solo si el proveedor limita). El timeout global de 15 s se
      // queda corto y aborta la petición sin respuesta; aquí se amplía a 2 min
      // solo para este endpoint.
      const { data } = await api.post<ContenidoBancoSaberPro[]>(
        `/saber-pro/docente/cursos/${curso.id}/contenido/generar/`,
        payload,
        { timeout: 120000 }
      )
      toast.success(
        data.length === 1
          ? 'Se generó 1 contenido pendiente de revisión'
          : `Se generaron ${data.length} contenidos pendientes de revisión`
      )
      reset()
      onGenerado()
      onCerrar()
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> }
        code?: string
      }
      const data = axiosErr.response?.data
      if (data) {
        toast.error(Object.values(data).flat().join('. '))
      } else if (axiosErr.code === 'ECONNABORTED') {
        toast.error('La generación tardó demasiado. Vuelve a intentarlo.')
      } else {
        toast.error('No se pudo generar el contenido')
      }
    } finally {
      setEnviando(false)
    }
  }

  const manejarCerrar = () => {
    reset()
    onCerrar()
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={`space-y-4 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
    >
      {/* Áreas estructuradas: competencia → afirmación → evidencia */}
      {tipo === 'competencias' && (
        <>
          <div className="space-y-1.5">
            <Label className={`${paletaSaberPro.titulo}`}>Competencia *</Label>
            <Controller
              control={control}
              name="competencia_id"
              render={({ field }) => (
                <Select
                  items={criterios.competencias.map((c) => ({ value: String(c.id), label: c.nombre }))}
                  value={field.value ?? ''}
                  onValueChange={(valor) => {
                    field.onChange(valor)
                    // Limpia los criterios dependientes al cambiar la competencia.
                    setValue('afirmacion_id', '')
                    setValue('evidencia_id', SIN_EVIDENCIA)
                  }}
                >
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Selecciona la competencia" />
                  </SelectTrigger>
                  <SelectContent className={selectContenidoAncho} alignItemWithTrigger={false}>
                    {criterios.competencias.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)} className={selectItemLargo}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.competencia_id && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.competencia_id.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label className={`${paletaSaberPro.titulo}`}>Afirmación *</Label>
            {/* `key={competenciaId}` remonta el Select al cambiar la competencia:
                evita que conserve el texto de una afirmación que ya no pertenece
                a la competencia elegida. */}
            <Controller
              control={control}
              name="afirmacion_id"
              render={({ field }) => (
                <Select
                  key={competenciaId}
                  items={afirmacionesDeCompetencia.map((a) => ({ value: String(a.id), label: a.nombre }))}
                  value={field.value ?? ''}
                  onValueChange={(valor) => {
                    field.onChange(valor)
                    // Limpia la evidencia dependiente al cambiar la afirmación.
                    setValue('evidencia_id', SIN_EVIDENCIA)
                  }}
                  disabled={afirmacionesDeCompetencia.length === 0}
                >
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Selecciona la afirmación" />
                  </SelectTrigger>
                  <SelectContent className={selectContenidoAncho} alignItemWithTrigger={false}>
                    {afirmacionesDeCompetencia.map((a) => (
                      <SelectItem key={a.id} value={String(a.id)} className={selectItemLargo}>
                        {a.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.afirmacion_id && (
              <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.afirmacion_id.message}</p>
            )}
          </div>

          {/* Evidencia opcional: muchas afirmaciones del catálogo no la definen. */}
          <div className="space-y-1.5">
            <Label className={`${paletaSaberPro.titulo}`}>
              Evidencia <span className={`text-xs font-normal ${paletaSaberPro.apoyo}`}>(opcional)</span>
            </Label>
            {/* `key={afirmacionId}` remonta el Select de evidencia al cambiar la
                afirmación, igual que en el caso de la afirmación. */}
            <Controller
              control={control}
              name="evidencia_id"
              render={({ field }) => (
                <Select
                  key={afirmacionId}
                  items={[
                    { value: SIN_EVIDENCIA, label: 'Sin evidencia específica' },
                    ...evidenciasDeAfirmacion.map((e) => ({ value: String(e.id), label: e.nombre })),
                  ]}
                  value={field.value ?? SIN_EVIDENCIA}
                  onValueChange={field.onChange}
                  disabled={evidenciasDeAfirmacion.length === 0}
                >
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Sin evidencia específica" />
                  </SelectTrigger>
                  <SelectContent className={selectContenidoAncho} alignItemWithTrigger={false}>
                    <SelectItem value={SIN_EVIDENCIA} className={selectItemLargo}>
                      Sin evidencia específica
                    </SelectItem>
                    {evidenciasDeAfirmacion.map((e) => (
                      <SelectItem key={e.id} value={String(e.id)} className={selectItemLargo}>
                        {e.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </>
      )}

      {/* Inglés: selector de la parte del examen (1 a 7) */}
      {tipo === 'partes' && (
        <div className="space-y-1.5">
          <Label className={`${paletaSaberPro.titulo}`}>Parte del examen *</Label>
          <Controller
            control={control}
            name="parte"
            render={({ field }) => (
              <Select
                items={criterios.partes.map((p) => ({
                  value: String(p.numero),
                  label: `Parte ${p.numero} · ${p.nombre} (${formaDeParte(p)})`,
                }))}
                value={field.value ?? ''}
                onValueChange={field.onChange}
              >
                <SelectTrigger className={selectTriggerLargo}>
                  <SelectValue placeholder="Selecciona la parte" />
                </SelectTrigger>
                <SelectContent className={selectContenidoAncho} alignItemWithTrigger={false}>
                  {criterios.partes.map((p) => (
                    <SelectItem key={p.numero} value={String(p.numero)} className={selectItemLargo}>
                      {p.numero}. {p.nombre} — {p.peso}% · {formaDeParte(p)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            />
            {errors.parte && <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.parte.message}</p>}
          </div>
      )}

      {/* Comunicación Escrita: aviso de que se generarán consignas de escritura. */}
      {tipo === 'consigna' && (
        <div className={`flex items-start gap-3 rounded-xl border p-4 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}>
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${paletaSaberPro.chipGold}`}>
            <Sparkles className="h-4 w-4" />
          </span>
          <p className={`text-xs leading-relaxed ${paletaSaberPro.texto}`}>
            Comunicación Escrita se prepara con <strong>consignas de escritura</strong>:
            la IA propondrá un tema y un contexto para que el estudiante argumente.
            No se seleccionan criterios.
          </p>
        </div>
      )}

      {/* Inglés: la parte completa se genera como un solo bloque del examen, así
          que no aplica elegir cantidad (su número de preguntas lo define el examen). */}
      {tipo === 'partes' && (
        <div className={`flex items-start gap-3 rounded-xl border p-4 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}>
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${paletaSaberPro.chipGold}`}>
            <Sparkles className="h-4 w-4" />
          </span>
          <p className={`text-xs leading-relaxed ${paletaSaberPro.texto}`}>
            Se generará la <strong>parte completa del examen</strong> en un solo bloque:
            la IA creará el texto (cuando la parte lo tiene) con todas sus preguntas,
            replicando la estructura del examen real.
          </p>
        </div>
      )}

      {/* Cantidad de piezas a generar (1 a 5); no aplica en Inglés. */}
      {tipo !== 'partes' && (
        <div className="space-y-1.5">
          <Label className={`${paletaSaberPro.titulo}`}>Cantidad a generar *</Label>
          <Controller
            control={control}
            name="cantidad"
            render={({ field }) => (
              <Select
                items={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: `${n} ${n === 1 ? 'pieza' : 'piezas'}` }))}
                value={field.value}
                onValueChange={field.onChange}
              >
                <SelectTrigger className={selectTriggerAncho}>
                  <SelectValue placeholder="Cantidad" />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <SelectItem key={n} value={String(n)}>
                      {n} {n === 1 ? 'pieza' : 'piezas'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.cantidad && <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.cantidad.message}</p>}
        </div>
      )}

      <div className={`border-t pt-4 ${paletaSaberPro.borde}`}>
        <p className={`flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
          <Sparkles className={`h-3.5 w-3.5 ${paletaSaberPro.accion}`} />
          El contenido se genera con IA y queda pendiente de tu revisión.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" className={`${paletaSaberPro.botonNeutro}`} onClick={manejarCerrar} disabled={enviando}>
            Cancelar
          </Button>
          <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={enviando}>
            {enviando ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generar contenido
              </>
            )}
          </Button>
        </div>
      </div>
    </form>
  )
}