// Sheet lateral para mostrar el perfil del usuario autenticado.
// Muestra: avatar con iniciales, nombre completo y email.
// Datos obtenidos de GET /usuarios/mis-datos/.
// Diseñado para futura edición de datos.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Loader2, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// Modelo de datos del perfil del usuario.
interface DatosPerfil {
  id: number
  first_name: string
  second_name: string
  first_last_name: string
  second_last_name: string
  email: string
}

interface SheetPerfilProps {
  abierto: boolean
  onCerrar: () => void
}

export function SheetPerfil({ abierto, onCerrar }: SheetPerfilProps) {
  const [datos, setDatos] = useState<DatosPerfil | null>(null)
  const [cargando, setCargando] = useState(false)

  // Carga los datos del perfil al abrir el sheet.
  useEffect(() => {
    if (!abierto) return

    const cargarPerfil = async () => {
      setCargando(true)
      try {
        const { data } = await api.get<DatosPerfil>('/usuarios/mis-datos/')
        setDatos(data)
      } catch {
        toast.error('No se pudieron cargar los datos del perfil')
      } finally {
        setCargando(false)
      }
    }
    cargarPerfil()
  }, [abierto])

  // Construye el nombre completo a partir de los campos del backend.
  const nombreCompleto = datos
    ? [datos.first_name, datos.second_name, datos.first_last_name, datos.second_last_name]
        .filter(Boolean)
        .join(' ')
    : ''

  // Genera las iniciales para el avatar (primera letra del nombre y primer apellido).
  const iniciales = datos
    ? `${datos.first_name?.[0] || ''}${datos.first_last_name?.[0] || ''}`.toUpperCase()
    : ''

  return (
    <Sheet open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <SheetContent side="right" className="w-80">
        <SheetHeader className="pb-6">
          <SheetTitle>Mi Perfil</SheetTitle>
          <SheetDescription>
            Información de tu cuenta
          </SheetDescription>
        </SheetHeader>

        {/* Estado de carga */}
        {cargando && (
          <div className="flex h-40 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Contenido del perfil */}
        {!cargando && datos && (
          <div className="space-y-6">
            {/* Avatar y nombre */}
            <div className="flex flex-col items-center text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 border border-primary/20 mb-3">
                <span className="text-lg font-bold text-primary">
                  {iniciales}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                {nombreCompleto}
              </h3>
              <p className="text-sm text-muted-foreground">
                {datos.email}
              </p>
            </div>

            {/* Datos en tarjeta */}
            <div className="rounded-xl border bg-card p-4 space-y-4">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Nombre
                </p>
                <p className="text-sm font-medium">
                  {datos.first_name} {datos.second_name}
                </p>
              </div>
              <div className="h-px bg-border" />
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Apellido
                </p>
                <p className="text-sm font-medium">
                  {datos.first_last_name} {datos.second_last_name}
                </p>
              </div>
              <div className="h-px bg-border" />
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Email
                </p>
                <p className="text-sm font-medium">
                  {datos.email}
                </p>
              </div>
            </div>

            {/* Botón editar (deshabilitado por ahora) */}
            <Button variant="outline" className="w-full" disabled>
              <Pencil className="h-4 w-4 mr-2" />
              Editar perfil (próximamente)
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
