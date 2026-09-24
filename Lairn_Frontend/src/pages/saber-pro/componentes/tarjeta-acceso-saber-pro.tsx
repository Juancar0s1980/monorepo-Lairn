// Tarjeta de acceso rápido al módulo Saber Pro para los dashboards (HU-16).
//
// Banner institucional de ancho completo que se inserta "sin rediseñar el
// resto": solo suma una invitación visual para entrar al módulo desde el panel
// principal (HU-16.1). Reutiliza la identidad del módulo (franja navy→dorado→
// naranja, sello circular, paleta de ./utilidades.ts) y navega a /saber-pro.

import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { GraduationCap, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'

interface TarjetaAccesoSaberProProps {
  /** Texto de apoyo bajo el título, adaptado al rol que lo muestra. */
  texto?: string
  /** Etiqueta del botón de acción (default: "Ir al módulo"). */
  etiquetaAccion?: string
}

// Texto por defecto cuando no se provee uno específico al rol.
const TEXTO_DEFAULT =
  'Simulacros con temporizador, contenido generado con IA y analítica de desempeño para la preparación de las pruebas Saber Pro.'

export function TarjetaAccesoSaberPro({
  texto = TEXTO_DEFAULT,
  etiquetaAccion = 'Ir al módulo',
}: TarjetaAccesoSaberProProps) {
  return (
    <section
      aria-label="Acceso rápido a Saber Pro"
      className={`relative overflow-hidden rounded-2xl border ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
    >
      {/* Franja institucional lateral navy → dorado → naranja */}
      <div
        aria-hidden="true"
        className="absolute inset-y-0 left-0 w-1.5 bg-gradient-to-b from-[#1e3a5f] via-[#c89b14] to-[#e8740e] dark:from-[#F3EDE1] dark:via-[#E3C063] dark:to-[#F29A52]"
      />
      <div className="flex flex-col gap-4 p-5 pl-6 sm:flex-row sm:items-center sm:justify-between sm:gap-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          {/* Sello circular con doble anillo, como en la portada del módulo */}
          <div className="relative flex h-14 w-14 shrink-0 items-center justify-center">
            <div
              aria-hidden="true"
              className={`absolute inset-0 rounded-full border border-dashed ${paletaSaberPro.badge}`}
            />
            <span
              className={`relative flex h-11 w-11 items-center justify-center rounded-full shadow-sm ${paletaSaberPro.sello}`}
            >
              <GraduationCap className="h-5 w-5" />
            </span>
          </div>
          <div>
            <p
              className={`text-[10px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}
            >
              Módulo Saber Pro
            </p>
            <h3 className={`mt-0.5 font-heading text-lg ${paletaSaberPro.titulo}`}>
              Prepárate para Saber Pro
            </h3>
            <p className={`mt-1 max-w-2xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              {texto}
            </p>
          </div>
        </div>
        <Link to="/saber-pro" className="shrink-0 self-start sm:self-center">
          <Button className={cn('h-9 gap-2 font-bold shadow-sm', paletaSaberPro.botonAccion)}>
            {etiquetaAccion}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </section>
  )
}