// Modal de gestión de un curso Saber Pro del docente (HU-17.3 a HU-17.6).
//
// Centraliza el refetch de los datos del curso con un `key` que cambia al
// modificar, y una consulta de estudiantes separada. Contiene:
//   - "Información" (HU-17.3): estable oficial del curso activo (activo/inactivo),
//     el código vigente con copia rápida y el botón regenerar (invalida el anterior).
//   - "Editar" (HU-17.4): cambia área, nombre y descripción.
//   - "Estudiantes" (HU-17.5): lista de inscritos con nombre, email y fecha.
//   - "Riesgo" (HU-17.6): desactiva el curso si conserva historial (la respuesta
//     indica cómo quedo) o lo elimina definitivamente si no.

import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Loader2, Copy, Check, RefreshCw, Edit3, Users, Trash2, GraduationCap, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'
import type { AreaSaberPro, CursoSaberPro, EstudianteInscrito } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

// Esquema de edición: área, nombre y descripción son editables (HU-17.4).
const esquemaEditarCurso = z.object({
  area_id: z.string().min(1, 'Selecciona el área'),
  nombre: z.string().min(1, 'El nombre es obligatorio').max(100, 'Máximo 100 caracteres'),
  descripcion: z.string().max(500, 'Máximo 500 caracteres').optional(),
})

type DatosEditarCurso = z.infer<typeof esquemaEditarCurso>

interface ModalDetalleCursoSaberProProps {
  /** Punto de partida del curso; el modal refetchea la versión vigente del backend. */
  curso: CursoSaberPro
  abierto: boolean
  onCerrar: () => void
  /** Se dispara tras cualquier mutación para que la lista del panel se refresque. */
  onCursoActualizado: () => void
}

export function ModalDetalleCursoSaberPro({
  curso,
  abierto,
  onCerrar,
  onCursoActualizado,
}: ModalDetalleCursoSaberProProps) {
  const [version, setVersion] = useState(curso)
  const [areas, setAreas] = useState<AreaSaberPro[]>([])
  const [estudiantes, setEstudiantes] = useState<EstudianteInscrito[]>([])
  const [segmento, setSegmento] = useState<'informacion' | 'editar' | 'estudiantes'>('informacion')
  const [enviando, setEnviando] = useState(false)
  const [copiado, setCopiado] = useState(false)
  const [refuerzo, setRefuerzo] = useState(false)
  const [confirmaRegenerar, setConfirmaRegenerar] = useState(false)
  const [confirmaEliminar, setConfirmaEliminar] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<DatosEditarCurso>({
    resolver: zodResolver(esquemaEditarCurso),
    values: {
      area_id: String(version.area.id),
      nombre: version.nombre,
      descripcion: version.descripcion,
    },
  })

  // Recarga el curso vigente, el catálogo de áreas y los estudiantes al abrir.
  useEffect(() => {
    if (!abierto) return
    const controlador = new AbortController()

    const cargar = async () => {
      try {
        const [{ data: cursoVigente }, { data: areasVigentes }, { data: estudiantesVigentes }] =
          await Promise.all([
            api.get<CursoSaberPro>(`/saber-pro/docente/cursos/${curso.id}/`, {
              signal: controlador.signal,
            }),
            api.get<AreaSaberPro[]>('/saber-pro/areas/', { signal: controlador.signal }),
            // Declara la intención de HU-17.5 desde la apertura; el backend resuelve si no hay.
            api.get<EstudianteInscrito[]>(`/saber-pro/docente/cursos/${curso.id}/estudiantes/`, {
              signal: controlador.signal,
            }),
          ])
        setVersion(cursoVigente)
        setAreas(areasVigentes)
        setEstudiantes(estudiantesVigentes)
        setSegmento('informacion')
      } catch {
        toast.error('No se pudo cargar el detalle del curso')
      }
    }

    cargar()
    return () => controlador.abort()
    // `curso.id` es la llave estable: al cambiar de curso el modal se recalcula.
  }, [abierto, curso.id])

  // Copia el código vigente al portapapeles (HU-17.3).
  const copiarCodigo = async () => {
    try {
      await navigator.clipboard.writeText(version.codigo)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      toast.error('No se pudo copiar el código')
    }
  }

  // Regenera el código: invalida el anterior y muestra el nuevo (HU-17.3).
  const regenerarCodigo = async () => {
    setEnviando(true)
    try {
      const { data } = await api.post<{ id: number; codigo: string; codigo_anterior: string }>(
        `/saber-pro/docente/cursos/${curso.id}/regenerar-codigo/`
      )
      setVersion((prev) => ({ ...prev, codigo: data.codigo }))
      setConfirmaRegenerar(false)
      toast.success('Código regenerado: el anterior dejó de ser válido')
      onCursoActualizado()
    } catch {
      toast.error('No se pudo regenerar el código')
    } finally {
      setEnviando(false)
    }
  }

  // Guarda los cambios de área/nombre/descripción (HU-17.4).
  const onSubmit = async (datos: DatosEditarCurso) => {
    setEnviando(true)
    try {
      const { data } = await api.put<CursoSaberPro>(`/saber-pro/docente/cursos/${curso.id}/`, {
        area_id: Number(datos.area_id),
        nombre: datos.nombre,
        descripcion: datos.descripcion || '',
      })
      setVersion(data)
      setSegmento('informacion')
      toast.success('Curso actualizado')
      onCursoActualizado()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo actualizar el curso')
    } finally {
      setEnviando(false)
    }
  }

  // Desactiva el curso (conserva historial) o lo elimina si no tiene (HU-17.6).
  const desactivarOEliminar = async () => {
    setEnviando(true)
    try {
      const { status: estadoHttp, data } = await api.delete<{ id?: number; activo?: boolean; detalle?: string }>(
        `/saber-pro/docente/cursos/${curso.id}/`
      )
      if (estadoHttp === 204) {
        toast.success('Curso eliminado')
      } else {
        if (data.activo === false) {
          toast.success('Curso desactivado porque conserva su historial')
        } else if (data.detalle) {
          toast.success('Curso desactivado porque conserva su historial')
        }
      }
      onCursoActualizado()
      onCerrar()
    } catch {
      toast.error('No se pudo eliminar el curso')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Dialog
      open={abierto}
      onOpenChange={(abre) => {
        if (!abre) {
          reset()
          onCerrar()
        }
      }}
    >
      <DialogContent className="max-w-2xl gap-0! overflow-hidden p-0! sm:max-h-[90vh] sm:overflow-y-auto">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <div className="flex items-start justify-between gap-3">
              <span
                className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.iconoChip}`}
              >
                <GraduationCap className="h-6 w-6" />
              </span>
              <Badge
                variant="outline"
                className={`${version.activo ? paletaSaberPro.badge : 'border-red-400/50 text-red-600 dark:text-red-300'}`}
              >
                {version.activo ? 'Activo' : 'Inactivo'}
              </Badge>
            </div>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {version.area.nombre}
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>{version.nombre}</DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              {version.descripcion || 'Sin descripción.'}
            </DialogDescription>
          </DialogHeader>

          {/* Segmentos de gestión del curso */}
          <div className={`mt-5 flex gap-1 rounded-xl border p-1 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
            {(
              [
                { clave: 'informacion', etiqueta: 'Información', icono: GraduationCap },
                { clave: 'editar', etiqueta: 'Editar', icono: Edit3 },
                { clave: 'estudiantes', etiqueta: 'Estudiantes', icono: Users },
              ] as const
            ).map(({ clave, etiqueta, icono: Icono }) => (
              <button
                key={clave}
                type="button"
                onClick={() => {
                  // Al cambiar de segmento se cortan los workflows de confirmación en curso.
                  setConfirmaRegenerar(false)
                  setConfirmaEliminar(false)
                  setRefuerzo(false)
                  setSegmento(clave)
                }}
                className={`flex h-9 flex-1 items-center justify-center gap-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  segmento === clave
                    ? `${paletaSaberPro.botonAccion}`
                    : `${paletaSaberPro.titulo} hover:bg-white dark:hover:bg-[#243A5E]`
                }`}
              >
                <Icono className="h-3.5 w-3.5" />
                {etiqueta}
              </button>
            ))}
          </div>
        </div>

        <div className={`border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
          {segmento === 'informacion' && (
            <div className="space-y-5">
              {/* HU-17.3: código vigente con copia y regeneración */}
              <div
                className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
              >
                <div>
                  <p className={`text-[10px] font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.apoyoTitulo}`}>
                    Código de acceso vigente
                  </p>
                  <p
                    className={`font-mono text-2xl font-bold tracking-[0.3em] ${paletaSaberPro.titulo}`}
                    aria-label={`Código de acceso ${version.codigo}`}
                  >
                    {version.codigo}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className={paletaSaberPro.botonNeutro}
                    onClick={copiarCodigo}
                    aria-label="Copiar código"
                  >
                    {copiado ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className={`gap-1.5 ${paletaSaberPro.botonAccion}`}
                    onClick={() => {
                      setRefuerzo(true)
                      setConfirmaRegenerar(true)
                    }}
                  >
                    <RefreshCw className="h-4 w-4" />
                    Regenerar
                  </Button>
                </div>
              </div>

              {confirmaRegenerar && (
                <div
                  className={`flex flex-col gap-3 rounded-xl border border-amber-400/40 p-4 ${paletaSaberPro.bandaAlterna}`}
                >
                  <p className={`flex items-center gap-2 text-sm font-medium ${paletaSaberPro.titulo}`}>
                    <ShieldAlert className="h-4 w-4 text-amber-500" />
                    ¿Regenerar el código? El código actual dejará de ser válido al instante.
                  </p>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" size="sm" className={paletaSaberPro.botonNeutro} onClick={() => setConfirmaRegenerar(false)}>
                      Cancelar
                    </Button>
                    <Button type="button" size="sm" className={paletaSaberPro.botonAccion} onClick={regenerarCodigo} disabled={enviando}>
                      {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Sí, regenerar'}
                    </Button>
                  </div>
                </div>
              )}

              {refuerzo && (
                <p className={`text-xs leading-relaxed ${paletaSaberPro.apoyo}`}>
                  Comparte el nuevo código con tus estudiantes: los que usen el
                  anterior ya no podrán unirse al curso.
                </p>
              )}

              {/* HU-17.6: zona de riesgo al pie del detalle */}
              <div className={`flex flex-col gap-3 rounded-xl border border-red-400/30 p-4 ${paletaSaberPro.bandaAlterna}`}>
                <div className="flex items-start gap-2">
                  <Trash2 className={`mt-0.5 h-4 w-4 shrink-0 text-red-500`} />
                  <div>
                    <p className={`text-sm font-semibold ${paletaSaberPro.titulo}`}>
                      Eliminar o desactivar curso
                    </p>
                    <p className={`mt-0.5 text-xs leading-relaxed ${paletaSaberPro.apoyo}`}>
                      Si el curso conserva simulacros o historial, se desactivará
                      conservando esos datos; si no, se eliminará por completo.
                    </p>
                  </div>
                </div>

                {!confirmaEliminar ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-9 self-end border-red-400/40 text-red-600 hover:text-red-700 dark:text-red-300"
                    onClick={() => setConfirmaEliminar(true)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Eliminar / desactivar
                  </Button>
                ) : (
                  <div className="flex flex-col gap-3">
                    <p className={`text-sm font-medium ${paletaSaberPro.titulo}`}>
                      Esta acción puede conservar el historial. ¿Deseas continuar?
                    </p>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" size="sm" className={paletaSaberPro.botonNeutro} onClick={() => setConfirmaEliminar(false)}>
                        Cancelar
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        className="h-9 border border-red-500 bg-red-600 text-white hover:bg-red-700"
                        onClick={desactivarOEliminar}
                        disabled={enviando}
                      >
                        {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Sí, continuar'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {segmento === 'editar' && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="area_id" className={paletaSaberPro.titulo}>
                  Área de Saber Pro *
                </Label>
                <Controller
                  control={control}
                  name="area_id"
                  render={({ field }) => (
                    <Select
                      items={areas.map((a) => ({ value: String(a.id), label: a.nombre }))}
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger className="w-full bg-white dark:bg-[#243A5E]">
                        <SelectValue placeholder="Selecciona el área" />
                      </SelectTrigger>
                      <SelectContent>
                        {areas.map((a) => (
                          <SelectItem key={a.id} value={String(a.id)}>
                            {a.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                {errors.area_id && <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.area_id.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="nombre" className={paletaSaberPro.titulo}>
                  Nombre del curso *
                </Label>
                <Input id="nombre" maxLength={100} className="bg-white dark:bg-[#243A5E]" {...register('nombre')} />
                {errors.nombre && <p className={`text-xs ${paletaSaberPro.accion}`}>{errors.nombre.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="descripcion" className={paletaSaberPro.titulo}>
                  Descripción
                </Label>
                <Textarea id="descripcion" rows={3} maxLength={500} className="bg-white dark:bg-[#243A5E]" {...register('descripcion')} />
              </div>

              <div className="flex justify-end gap-2 border-t pt-4" style={{ borderColor: 'rgba(30,58,95,0.09)' }}>
                <Button type="button" className={paletaSaberPro.botonNeutro} onClick={() => setSegmento('informacion')}>
                  Cancelar
                </Button>
                <Button type="submit" className={`gap-2 ${paletaSaberPro.botonAccion}`} disabled={enviando}>
                  {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Edit3 className="h-4 w-4" />}
                  Guardar cambios
                </Button>
              </div>
            </form>
          )}

          {segmento === 'estudiantes' && (
            <div>
              <p className={`flex items-center gap-2 text-sm font-medium ${paletaSaberPro.titulo}`}>
                <Users className="h-4 w-4" />
                Estudiantes inscritos ({estudiantes.length})
              </p>
              {estudiantes.length === 0 ? (
                <p className={`mt-4 rounded-xl border border-dashed p-6 text-center text-sm ${paletaSaberPro.borde} ${paletaSaberPro.apoyo}`}>
                  Aún no hay estudiantes inscritos. Comparte el código para que se unan (HU-18).
                </p>
              ) : (
                <Table className="mt-4">
                  <TableHeader>
                    <TableRow>
                      <TableHead className={paletaSaberPro.titulo}>Estudiante</TableHead>
                      <TableHead className={paletaSaberPro.titulo}>Correo</TableHead>
                      <TableHead className={`text-right ${paletaSaberPro.titulo}`}>Fecha de ingreso</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {estudiantes.map((inscripcion) => (
                      <TableRow key={inscripcion.id}>
                        <TableCell className={paletaSaberPro.texto}>
                          {inscripcion.estudiante.nombre_completo}
                        </TableCell>
                        <TableCell className={paletaSaberPro.apoyo}>{inscripcion.estudiante.email}</TableCell>
                        <TableCell className={`text-right ${paletaSaberPro.apoyo}`}>
                          {new Date(inscripcion.fecha).toLocaleDateString('es-CO', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}