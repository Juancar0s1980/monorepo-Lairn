// Sección de cursos Saber Pro a los que el estudiante pertenece (HU-18.3).
//
// Se monta dentro del panel cuando el estudiante ya tiene inscripciones
// (`tiene_cursos: true`). Lista cada curso de preparación al que se unió con el
// código de acceso, mostrando el área, el nombre, la fecha de ingreso y el
// estado (activo/inactivo). Modular y reutilizable: la misma fuente de verdad
// (las inscripciones del estudiante) la consumirán HU-19.5 y HU-23/24.

import { AlertCircle, CalendarDays, GraduationCap, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useCursosEstudianteSaberPro } from '@/hooks/use-cursos-estudiante-saber-pro'
import type { InscripcionCursoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

// Formatea la fecha de ingreso a un texto legible en español (ej. "14 de marzo de 2026").
function formatearFecha(iso: string): string {
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return iso
  return fecha.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
}

// Tarjeta compacta de un curso al que el estudiante se unió (HU-18.3).
function TarjetaCursoEstudiante({ inscripcion }: { inscripcion: InscripcionCursoSaberPro }) {
  const { curso } = inscripcion
  return (
    <li
      className={`flex flex-col gap-3 rounded-2xl border p-4 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${paletaSaberPro.chipGold}`}>
          <GraduationCap className="h-5 w-5" />
        </span>
        <Badge variant="outline" className={`text-[11px] font-semibold ${paletaSaberPro.badge}`}>
          {curso.area.nombre}
        </Badge>
      </div>

      <div className="min-w-0">
        <p className={`truncate text-sm font-bold ${paletaSaberPro.titulo}`}>{curso.nombre}</p>
        <p className={`mt-1 line-clamp-2 text-xs leading-relaxed ${paletaSaberPro.apoyo}`}>
          {curso.descripcion || 'Sin descripción.'}
        </p>
      </div>

      <div className={`mt-auto flex items-center justify-between gap-2 pt-1`}>
        {curso.activo ? (
          <p className={`inline-flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
            <CalendarDays className={`h-3.5 w-3.5 ${paletaSaberPro.separador}`} />
            Ingresaste el {formatearFecha(inscripcion.fecha)}
          </p>
        ) : (
          <Badge variant="outline" className="h-5 border-red-400/50 text-[10px] text-red-600 dark:text-red-300">
            Curso desactivado
          </Badge>
        )}
      </div>
    </li>
  )
}

// Lista las inscripciones del estudiante con su estado de carga y error.
export function SeccionCursosEstudianteSaberPro() {
  const { inscripciones, cargando, error, recargar } = useCursosEstudianteSaberPro()

  if (cargando) {
    return (
      <div aria-busy="true" className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className={`h-24 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
          />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className={`mt-6 flex items-center justify-between gap-4 rounded-2xl border p-4 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}>
        <p className={`flex items-center gap-2 text-sm ${paletaSaberPro.apoyo}`}>
          <AlertCircle className={`h-4 w-4 ${paletaSaberPro.accion}`} />
          {error}
        </p>
        <Button type="button" className={`${paletaSaberPro.botonNeutro}`} onClick={() => void recargar()}>
          Reintentar
        </Button>
      </div>
    )
  }

  if (inscripciones.length === 0) {
    return (
      <p className={`mt-4 rounded-2xl border border-dashed p-5 text-sm leading-relaxed ${paletaSaberPro.borde} ${paletaSaberPro.texto}`}>
        Aún no te has unido a ningún curso de preparación.
      </p>
    )
  }

  return (
    <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {inscripciones.map((inscripcion) => (
        <TarjetaCursoEstudiante key={inscripcion.id} inscripcion={inscripcion} />
      ))}
    </ul>
  )
}

// Nota de seguridad del flujo de inscripción por código (HU-18).
export function NotaInscripcionPorCodigo() {
  return (
    <p
      className={`mt-5 inline-flex flex-wrap items-center gap-2 rounded-full border px-4 py-1.5 text-xs ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde} ${paletaSaberPro.apoyo}`}
    >
      <ShieldCheck className={`h-3.5 w-3.5 shrink-0 ${paletaSaberPro.accion}`} />
      Te uniste a estos cursos con el código que te compartió tu docente.
    </p>
  )
}