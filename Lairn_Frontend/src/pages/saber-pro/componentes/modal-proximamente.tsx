// Modal de "próximamente" para las acciones del estado vacío de HU-16.3.
//
// Las opciones "Crear curso" (docente) y "Unirme con código" (estudiante) del
// estado vacío apuntan a funcionalidades de las épicas HU-17 y HU-18, que se
// implementan en entregas posteriores. Por eso este modal aclara al usuario
// que la acción ya está contemplada en la ruta del módulo y le indica a qué
// épica pertenece, sin dejar el botón sin respuesta.

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Rocket, KeyRound, BookMarked } from 'lucide-react'
import type { AccionVaciaSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'

// Épica de Saber Pro que implementa cada acción del estado vacío.
const EPICA_POR_ACCION: Record<AccionVaciaSaberPro['tipo'], { etiqueta: string; texto: string }> = {
  crear_curso: {
    etiqueta: 'HU-17',
    texto:
      'La creación de cursos Saber Pro (área, nombre, descripción y código de acceso auto-generado) llega en la entrega HU-17. Tu docente no escribirá el código: el sistema lo asignará automáticamente.',
  },
  unirse_codigo: {
    etiqueta: 'HU-18',
    texto:
      'La inscripción con código de acceso a un curso Saber Pro llega en la entrega HU-18. Pide a tu docente el código vigente de su curso para unirte cuando la funcionalidad esté disponible.',
  },
}

interface ModalProximamenteProps {
  /** Acción del estado vacío que abrió el modal (define título y épica). */
  accion: AccionVaciaSaberPro | null
  abierto: boolean
  onCerrar: () => void
}

export function ModalProximamente({ accion, abierto, onCerrar }: ModalProximamenteProps) {
  const epica = accion ? EPICA_POR_ACCION[accion.tipo] : null
  const Icono = accion?.tipo === 'crear_curso' ? BookMarked : KeyRound

  return (
    <Dialog
      open={abierto}
      onOpenChange={(abre: boolean) => {
        // Se cierra solo con el botón "Entendido" para no perder el contexto.
        if (!abre) onCerrar()
      }}
    >
      {/* p-0! deja el contenido "full-bleed": encabezado sobre superficie y pie
          sobre la banda institucional, sin el padding por defecto del diálogo. */}
      <DialogContent className="max-w-sm gap-0! overflow-hidden p-0!">
        <div className={`p-6 pb-5 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <div className="flex items-start justify-between gap-3">
              <span
                className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}
              >
                <Icono className="h-6 w-6" />
              </span>
              <Badge
                variant="outline"
                className={`text-[11px] font-semibold ${paletaSaberPro.badge}`}
              >
                {epica?.etiqueta}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Rocket className={`h-4 w-4 ${paletaSaberPro.accion}`} aria-hidden="true" />
              <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
                Muy pronto
              </p>
            </div>
            <DialogTitle className={`text-lg ${paletaSaberPro.titulo}`}>
              {accion?.titulo ?? 'Funcionalidad en camino'}
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              {epica?.texto}
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Pie sobre la banda institucional (beige ↔ navy), ajeno a DialogFooter
            para controlar el fondo con los tokens del módulo */}
        <div
          className={`border-t px-6 py-3.5 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}
        >
          <Button className={`w-full ${paletaSaberPro.botonNeutro}`} onClick={onCerrar}>
            Entendido
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}