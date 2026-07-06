// Hook para consumir el contexto de autenticación.
// Separado del proveedor para cumplir react-refresh (un archivo = un componente).

import { useContext } from 'react'
import { AuthContext } from './contexto'

// Hook para consumir el contexto de autenticación.
// Lanza error si se usa fuera de un ProveedorAuth.
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de ProveedorAuth')
  }
  return context
}
