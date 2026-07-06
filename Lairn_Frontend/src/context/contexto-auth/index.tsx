// Contexto de autenticación de la aplicación.
// Provee a toda la app el estado del usuario autenticado y funciones
// para iniciar sesión, registrar y cerrar sesión.
// Al montar, intenta cargar el usuario actual desde /usuarios/mis-datos/
// usando el access token guardado en localStorage.

import { useState, useEffect, useCallback, type ReactNode } from 'react'
import api from '@/services/api'
import type { Usuario } from '@/types/usuario'
import type { LoginRequest, LoginResponse, RegistroRequest, AuthState } from '@/types/auth'
import { obtenerRolDelToken } from '@/utilities/token'
import { AuthContext } from './contexto'

// Proveedor que envuelve la app y gestiona el estado de autenticación.
export function ProveedorAuth({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<AuthState>({
    usuario: null,
    estaAutenticado: false,
    estaCargando: true, // true inicialmente para evitar parpadeo al verificar token
    rol: undefined,
  })

  // Intenta obtener los datos del usuario autenticado desde el backend.
  // Si no hay token o la petición falla, limpia los tokens y marca como no autenticado.
  const cargarUsuario = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setEstado({ usuario: null, estaAutenticado: false, estaCargando: false, rol: undefined })
      return
    }

    try {
      const { data } = await api.get<Usuario>('/usuarios/mis-datos/')
      setEstado({ usuario: data, estaAutenticado: true, estaCargando: false, rol: obtenerRolDelToken() })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setEstado({ usuario: null, estaAutenticado: false, estaCargando: false, rol: undefined })
    }
  }, [])

  // Al montar el proveedor, intentar cargar el usuario existente.
  // Se usa un patrón con flag para evitar setState después de desmontar.
  useEffect(() => {
    let activo = true
    const cargar = async () => {
      const token = localStorage.getItem('access_token')
      if (!token) {
        if (activo) setEstado({ usuario: null, estaAutenticado: false, estaCargando: false, rol: undefined })
        return
      }

      try {
        const { data } = await api.get<Usuario>('/usuarios/mis-datos/')
        if (activo) setEstado({ usuario: data, estaAutenticado: true, estaCargando: false, rol: obtenerRolDelToken() })
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        if (activo) setEstado({ usuario: null, estaAutenticado: false, estaCargando: false, rol: undefined })
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  // Login: envía credenciales al backend, guarda tokens y recarga datos del usuario.
  const iniciarSesion = async (credenciales: LoginRequest) => {
    const { data } = await api.post<LoginResponse>('/usuarios/iniciar-sesion/', credenciales)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    await cargarUsuario()
  }

  // Registro: crea la cuenta y automáticamente hace login con las mismas credenciales.
  const registrar = async (datos: RegistroRequest) => {
    await api.post('/usuarios/registrar/', datos)
    await iniciarSesion({ email: datos.email, password: datos.password })
  }

  // Logout: notifica al backend para blacklistear el refresh token,
  // luego limpia los tokens del localStorage y resetea el estado.
  const cerrarSesion = async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        await api.post('/usuarios/cerrar-sesion/', { refresh: refreshToken })
      } catch {
        // Ignorar errores del backend, limpiar localmente de todas formas
      }
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setEstado({ usuario: null, estaAutenticado: false, estaCargando: false, rol: undefined })
  }

  return (
    <AuthContext.Provider value={{ ...estado, iniciarSesion, registrar, cerrarSesion }}>
      {children}
    </AuthContext.Provider>
  )
}
