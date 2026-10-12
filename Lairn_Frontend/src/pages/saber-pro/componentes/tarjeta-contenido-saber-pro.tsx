// Tarjeta de una pieza del banco de contenido Saber Pro (HU-20.3).
//
// Muestra una pregunta de selección múltiple o una consigna de escritura con su
// estado de revisión y sus criterios. Para el contenido `pendiente` ofrece las
// acciones de la HU-20.3 —aprobar, editar y descartar—; el contenido `aprobado`
// solo se muestra (ya forma parte del banco de los simulacros).
//
// La aprobación (PATCH .../aprobar/) y el descarte (DELETE) se ejecutan aquí;
// la edición abre `ModalEditarContenidoSaberPro`. Tras cualquier mutación se
// notifica al padre con `onCambio()` para refrescar el banco.

import { useState } from 'react'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { CheckCircle2, Pencil, Trash2, Loader2, Languages, PenLine, BookOpen, Lock } from 'lucide-react'
import { toast } from 'sonner'
import type { ContenidoBancoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'
import { ModalEditarContenidoSaberPro } from './modal-editar-contenido-saber-pro'

interface TarjetaContenidoSaberProProps {
  contenido: ContenidoBancoSaberPro
  /** Se invoca tras aprobar, descartar o editar para refrescar el banco. */
  onCambio: () => void
}

export function TarjetaContenidoSaberPro({ contenido, onCambio }: TarjetaContenidoSaberProProps) {
  const [aprobando, setAprobando] = useState(false)
  const [descartando, setDescartando] = useState(false)
  const [confirmarDescarte, setConfirmarDescarte] = useState(false)
  const [editarAbierto, setEditarAbierto] = useState(false)

  const esPregunta = contenido.tipo === 'seleccion_multiple'
  // Parte 1 de Inglés: tarea de relacionar (8 palabras para 5 descripciones),
  // no es una pregunta de opción múltiple con una única respuesta correcta.
  const esRelacion = esPregunta && contenido.parte === 1
  const parte = contenido.parte
  // Partes 2 a 7 de Inglés: el contenido es la parte COMPLETA del examen, un
  // bloque con todas sus preguntas en `preguntas` (texto base + preguntas en
  // las partes 4 a 7; preguntas autocontenidas en las 2 y 3).
  const esBloqueIngles =
    esPregunta && parte !== null && parte !== 1 && contenido.preguntas.length > 0
  // Contenido generado antes del esquema de `relaciones`: el docente debe
  // descartarlo y regenerarlo porque el backend ya no lo considera válido.
  const esRelacionLegacy = esRelacion && contenido.relaciones.length === 0
  // Partes 2 a 7 generadas antes del esquema de `preguntas`: eran una sola
  // pregunta de opción múltiple y hoy el formato exige el bloque completo.
  const esBloqueLegacy =
    esPregunta && parte !== null && parte !== 1 && contenido.preguntas.length === 0 && contenido.opciones.length > 0
  const sobrantes = contenido.opciones.length - contenido.relaciones.length
  const aprobado = contenido.estado === 'aprobado'

  // Aprueba el contenido para que pueda usarse en los simulacros (HU-20.4).
  const aprobar = async () => {
    setAprobando(true)
    try {
      await api.patch(`/saber-pro/docente/contenido/${contenido.id}/aprobar/`)
      toast.success('Contenido aprobado')
      onCambio()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo aprobar el contenido')
    } finally {
      setAprobando(false)
    }
  }

  // Descarta definitivamente un contenido pendiente.
  const descartar = async () => {
    setDescartando(true)
    try {
      await api.delete(`/saber-pro/docente/contenido/${contenido.id}/`)
      toast.success('Contenido descartado')
      setConfirmarDescarte(false)
      onCambio()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } }
      const data = axiosErr.response?.data
      toast.error(data ? Object.values(data).flat().join('. ') : 'No se pudo descartar el contenido')
    } finally {
      setDescartando(false)
    }
  }

  // Etiqueta de criterio: parte de Inglés, área de consigna o jerarquía competencial.
  const etiquetaCriterio = contenido.parte
    ? `Parte ${contenido.parte}`
    : contenido.competencia?.nombre ?? 'Consigna de escritura'

  return (
    <article
      className={`flex flex-col gap-3 rounded-2xl border p-5 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      {/* Cabecera: tipo + estado */}
      <header className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={`gap-1.5 ${paletaSaberPro.badge}`}>
          {esPregunta ? <BookOpen className="h-3.5 w-3.5" /> : <PenLine className="h-3.5 w-3.5" />}
          {esRelacion ? 'Relacionar' : esBloqueIngles ? 'Bloque' : esPregunta ? 'Pregunta' : 'Consigna'}
        </Badge>
        {contenido.parte && (
          <Badge variant="outline" className={`gap-1.5 ${paletaSaberPro.badge}`}>
            <Languages className="h-3.5 w-3.5" />
            {etiquetaCriterio}
          </Badge>
        )}
        {!contenido.parte && contenido.competencia && (
          // La competencia puede tener un nombre largo: en vez de recortarlo se
          // permite que el badge crezca en varias líneas (por defecto el Badge
          // usa `h-5` + `overflow-hidden` + `whitespace-nowrap`).
          <Badge
            variant="outline"
            className={`h-auto! max-w-full min-w-0 shrink py-1! text-left whitespace-normal break-words ${paletaSaberPro.badge}`}
          >
            {etiquetaCriterio}
          </Badge>
        )}
        {aprobado ? (
          <Badge className="ml-auto gap-1.5 border-transparent bg-emerald-600/15 text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Aprobado
          </Badge>
        ) : (
          <Badge variant="outline" className={`ml-auto gap-1.5 ${paletaSaberPro.badge}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
            Pendiente
          </Badge>
        )}
      </header>

      {/* Jerarquía competencial (solo áreas estructuradas) */}
      {(contenido.afirmacion || contenido.evidencia) && (
        <ul className={`break-words space-y-0.5 text-xs ${paletaSaberPro.apoyo}`}>
          {contenido.competencia && <li className="break-words">Competencia: {contenido.competencia.nombre}</li>}
          {contenido.afirmacion && <li className="break-words">Afirmación: {contenido.afirmacion.nombre}</li>}
          {contenido.evidencia && <li className="break-words">Evidencia: {contenido.evidencia.nombre}</li>}
        </ul>
      )}

      {/* Consigna: tema + contexto */}
      {!esPregunta && contenido.tema && (
        <p className={`text-sm font-semibold ${paletaSaberPro.titulo}`}>{contenido.tema}</p>
      )}

      {/* Contexto / texto base */}
      {contenido.contexto && (
        <p className={`break-words whitespace-pre-line text-xs leading-relaxed ${paletaSaberPro.texto}`}>{contenido.contexto}</p>
      )}

      {/* Enunciado */}
      <p className={`break-words text-sm font-medium leading-relaxed ${paletaSaberPro.titulo}`}>{contenido.enunciado}</p>

      {/* Opciones con la respuesta correcta resaltada (selección múltiple) */}
      {esPregunta && !esRelacion && !esBloqueIngles && contenido.opciones.length > 0 && (
        <ul className="space-y-1.5">
          {contenido.opciones.map((opcion, indice) => {
            const correcta = opcion === contenido.respuesta_correcta
            return (
              <li
                key={indice}
                className={`flex items-start gap-2 rounded-lg border px-3 py-1.5 text-xs ${
                  correcta
                    ? 'border-[#c89b14]/50 bg-[#c89b14]/10 dark:border-[#E3C063]/50 dark:bg-[#E3C063]/10'
                    : `${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`
                }`}
              >
                <span className={`font-bold ${correcta ? paletaSaberPro.titulo : paletaSaberPro.apoyo}`}>
                  {String.fromCharCode(65 + indice)}.
                </span>
                <span className={`min-w-0 break-words ${correcta ? paletaSaberPro.titulo : paletaSaberPro.texto}`}>{opcion}</span>
                {correcta && <CheckCircle2 className={`ml-auto h-3.5 w-3.5 shrink-0 ${paletaSaberPro.accion}`} />}
              </li>
            )
          })}
        </ul>
      )}

      {/* Parte 1 de Inglés: relacionar 5 descripciones con 8 palabras (A-H) */}
      {esRelacion && !esRelacionLegacy && (
        <>
          <div>
            <p className={`mb-1.5 text-[11px] font-semibold uppercase tracking-wide ${paletaSaberPro.apoyoTitulo}`}>
              Palabras (A a H)
            </p>
            <ul className="flex flex-wrap gap-1.5">
              {contenido.opciones.map((palabra, indice) => (
                <li
                  key={indice}
                  className={`rounded-lg border px-2 py-1 text-xs ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
                >
                  <span className={`font-bold ${paletaSaberPro.apoyo}`}>{String.fromCharCode(65 + indice)}.</span>{' '}
                  <span className={`break-words ${paletaSaberPro.texto}`}>{palabra}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className={`mb-1.5 text-[11px] font-semibold uppercase tracking-wide ${paletaSaberPro.apoyoTitulo}`}>
              Descripciones relacionadas
            </p>
            <ul className="space-y-1.5">
              {contenido.relaciones.map((relacion, indice) => (
                <li
                  key={indice}
                  className="flex items-start gap-2 rounded-lg border border-[#c89b14]/50 bg-[#c89b14]/10 px-3 py-1.5 text-xs dark:border-[#E3C063]/50 dark:bg-[#E3C063]/10"
                >
                  <span className={`shrink-0 font-bold ${paletaSaberPro.titulo}`}>{indice + 1}.</span>
                  <span className={`min-w-0 flex-1 break-words ${paletaSaberPro.texto}`}>{relacion.descripcion}</span>
                  <span className={`flex shrink-0 items-center gap-1 font-semibold ${paletaSaberPro.titulo}`}>
                    {relacion.respuesta}
                    <CheckCircle2 className={`h-3.5 w-3.5 shrink-0 ${paletaSaberPro.accion}`} />
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {sobrantes > 0 && (
            <p className={`text-xs ${paletaSaberPro.apoyo}`}>
              {sobrantes} {sobrantes === 1 ? 'palabra queda' : 'palabras quedan'} sin usar
              (distractor{sobrantes === 1 ? '' : 'es'}).
            </p>
          )}
        </>
      )}

      {/* Parte 1 generada antes del esquema de relaciones: formato obsoleto. */}
      {esRelacionLegacy && (
        <p className={`rounded-lg border px-3 py-2 text-xs ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde} ${paletaSaberPro.apoyo}`}>
          Este contenido tiene formato antiguo de opción múltiple: descártalo y vuelve a generarlo
          para obtener la tarea de relacionar.
        </p>
      )}

      {/* Partes 2 a 7 generadas antes del esquema de `preguntas`: una sola
          pregunta en lugar del bloque completo del examen. */}
      {esBloqueLegacy && (
        <p className={`rounded-lg border px-3 py-2 text-xs ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde} ${paletaSaberPro.apoyo}`}>
          Este contenido tiene formato antiguo de una sola pregunta: descártalo y vuelve a generarlo
          para obtener la parte completa del examen.
        </p>
      )}

      {/* Partes 2 a 7 de Inglés: preguntas del bloque completo del examen.
          `enunciado` es la instrucción general y cada pregunta lleva su contexto
          propio (avisos/conversaciones) o depende del `contexto` compartido
          (texto base de las partes 4 a 7). */}
      {esBloqueIngles && (
        <div className="space-y-3">
          <p className={`text-[11px] font-semibold uppercase tracking-wide ${paletaSaberPro.apoyoTitulo}`}>
            Preguntas del bloque ({contenido.preguntas.length})
          </p>
          {contenido.preguntas.map((pregunta, indice) => (
            <div
              key={indice}
              className={`space-y-1.5 rounded-xl border p-3 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
            >
              <p className={`break-words text-xs leading-relaxed ${paletaSaberPro.titulo}`}>
                <span className={`mr-1 font-bold ${paletaSaberPro.apoyo}`}>{indice + 1}.</span>
                {pregunta.enunciado}
              </p>
              <ul className="space-y-1">
                {pregunta.opciones.map((opcion, i) => {
                  const correcta = opcion === pregunta.respuesta_correcta
                  return (
                    <li
                      key={i}
                      className={`flex items-start gap-2 rounded-lg border px-3 py-1.5 text-xs ${
                        correcta
                          ? 'border-[#c89b14]/50 bg-[#c89b14]/10 dark:border-[#E3C063]/50 dark:bg-[#E3C063]/10'
                          : `${paletaSaberPro.banda} ${paletaSaberPro.borde}`
                      }`}
                    >
                      <span className={`font-bold ${correcta ? paletaSaberPro.titulo : paletaSaberPro.apoyo}`}>
                        {String.fromCharCode(65 + i)}.
                      </span>
                      <span className={`min-w-0 break-words ${correcta ? paletaSaberPro.titulo : paletaSaberPro.texto}`}>
                        {opcion}
                      </span>
                      {correcta && <CheckCircle2 className={`ml-auto h-3.5 w-3.5 shrink-0 ${paletaSaberPro.accion}`} />}
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* Acciones: solo el contenido pendiente se puede revisar (HU-20.3). */}
      <footer className={`mt-auto flex flex-wrap items-center gap-2 border-t pt-3 ${paletaSaberPro.borde}`}>
        {aprobado ? (
          <span className={`flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
            <Lock className="h-3.5 w-3.5" />
            Aprobado y disponible para los simulacros
          </span>
        ) : (
          <>
            <Button
              type="button"
              className={`h-8 gap-1.5 px-3 text-xs font-bold ${paletaSaberPro.botonAccion}`}
              onClick={aprobar}
              disabled={aprobando || descartando}
            >
              {aprobando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
              Aprobar
            </Button>
            <Button
              type="button"
              className={`h-8 gap-1.5 px-3 text-xs ${paletaSaberPro.botonNeutro}`}
              onClick={() => setEditarAbierto(true)}
              disabled={aprobando || descartando}
            >
              <Pencil className="h-3.5 w-3.5" />
              Editar
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="h-8 gap-1.5 px-3 text-xs text-destructive hover:text-destructive"
              onClick={() => setConfirmarDescarte(true)}
              disabled={aprobando || descartando}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Descartar
            </Button>
          </>
        )}
      </footer>

      {/* Confirmación de descarte: acción irreversible sobre el banco. */}
      <Dialog open={confirmarDescarte} onOpenChange={(abre) => !abre && setConfirmarDescarte(false)}>
        <DialogContent className="max-w-[calc(100%-1.5rem)] sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className={`text-lg ${paletaSaberPro.titulo}`}>Descartar contenido</DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Esta acción elimina la pieza del banco y no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              className={`${paletaSaberPro.botonNeutro}`}
              onClick={() => setConfirmarDescarte(false)}
              disabled={descartando}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              className="gap-2 bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={descartar}
              disabled={descartando}
            >
              {descartando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Descartar
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edición del contenido pendiente (HU-20.3). */}
      <ModalEditarContenidoSaberPro
        abierta={editarAbierto}
        contenido={contenido}
        onCerrar={() => setEditarAbierto(false)}
        onActualizado={onCambio}
      />
    </article>
  )
}