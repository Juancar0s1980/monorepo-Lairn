// Estado vacío del panel de Saber Pro (HU-16.3).
//
// Se muestra cuando el usuario aún no tiene cursos Saber Pro (`tiene_cursos:
// false`). Presenta una invitación clara según el rol —"Crear curso" para el
// docente (navega a /saber-pro/cursos, HU-17) y "Unirme con código" para el
// estudiante (abre el modal de inscripción por código, HU-18)— para que el
// usuario sepa cómo empezar a usar el módulo. El diseño respeta la identidad
// institucional (fondo beige, acentos navy/dorado/naranja) y es consistente en
// claro y oscuro.

import { Button } from '@/components/ui/button'
import { ArrowRight, BookMarked, KeyRound, ShieldCheck } from 'lucide-react'
import type { AccionVaciaSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

interface EstadoVacioSaberProProps {
  accion: AccionVaciaSaberPro | null
  onAccion: () => void
}

export function EstadoVacioSaberPro({ accion, onAccion }: EstadoVacioSaberProProps) {
  const Icono = accion?.tipo === 'crear_curso' ? BookMarked : KeyRound
  const esDocente = accion?.tipo === 'crear_curso'

  return (
    <section aria-labelledby="estado-vacio-saber-pro" className="mt-10">
      <div
        className={`relative overflow-hidden rounded-3xl border p-8 text-center md:p-12 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
      >
        {/* Halos decorativos que enmarcan la invitación */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-20 -left-16 h-56 w-56 rounded-full bg-radial from-[#1e3a5f]/10 to-transparent dark:from-[#F3EDE1]/8"
        />

        <div className="relative mx-auto flex max-w-2xl flex-col items-center">
          {/* Anillo + chip de icono: refuerza que es el punto de partida del módulo */}
          <div className="relative flex h-24 w-24 items-center justify-center" aria-hidden="true">
            <div className={`absolute inset-0 rounded-full border-2 border-dashed ${paletaSaberPro.badge}`} />
            <div className={`absolute inset-2.5 rounded-full border ${paletaSaberPro.borde}`} />
            <span
              className={`relative flex h-16 w-16 items-center justify-center rounded-full ${paletaSaberPro.iconoChip}`}
            >
              <Icono className="h-8 w-8" />
            </span>
          </div>

          <p
            className={`mt-6 flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}
          >
            <span className={`h-px w-6 ${paletaSaberPro.separador}`} aria-hidden="true" />
            Empieza aquí
            <span className={`h-px w-6 ${paletaSaberPro.separador}`} aria-hidden="true" />
          </p>

          <h2
            id="estado-vacio-saber-pro"
            className={`mt-3 text-[clamp(1.6rem,3.5vw,2.4rem)] font-extrabold leading-tight tracking-tight text-balance ${paletaSaberPro.titulo}`}
          >
            {accion?.titulo ?? 'Empieza en Saber Pro'}
          </h2>

          <p className={`mt-4 max-w-xl text-base leading-relaxed ${paletaSaberPro.texto}`}>
            {accion?.descripcion}
          </p>

          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
            <Button
              onClick={onAccion}
              className={`h-11 gap-2 px-6 font-bold shadow-md ${paletaSaberPro.botonAccion}`}
            >
              {accion?.etiqueta_accion ?? 'Comenzar'}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Nota de confianza: el código siempre lo asigna el sistema, nunca el docente */}
          <p
            className={`mt-8 inline-flex max-w-md items-center gap-2 rounded-full border px-4 py-1.5 text-xs ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde} ${paletaSaberPro.apoyo}`}
          >
            <ShieldCheck className={`h-3.5 w-3.5 shrink-0 ${paletaSaberPro.accion}`} />
            {esDocente
              ? 'El código de acceso se genera automáticamente: tú solo defines área, nombre y descripción.'
              : 'El código te lo comparte tu docente y es único para cada curso de preparación.'}
          </p>
        </div>
      </div>
    </section>
  )
}