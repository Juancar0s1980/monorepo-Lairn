// Componente guardia que protege rutas según autenticación y rol.
// - Muestra spinner mientras carga el estado de auth.
// - Redirige a /iniciar-sesion si no está autenticado.
// - Redirige a / si el rol del usuario no está en rolesPermitidos.

import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/contexto-auth/use-auth'
import type { ReactNode } from 'react'

interface RutaProtegidaProps {
  children: ReactNode
  rolesPermitidos?: string[]
}

export function RutaProtegida({ children, rolesPermitidos }: RutaProtegidaProps) {
  const { estaAutenticado, estaCargando, rol } = useAuth()

  if (estaCargando) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!estaAutenticado) {
    return <Navigate to="/iniciar-sesion" replace />
  }

  if (rolesPermitidos && rol) {
    if (!rolesPermitidos.includes(rol)) {
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
