// Definición del contexto de autenticación.
// Separado en su propio archivo para que tanto el proveedor como el hook lo importen.

import { createContext } from 'react'
import type { LoginRequest, RegistroRequest, AuthState } from '@/types/auth'

// Forma del contexto: estado de auth + funciones para login/registro/logout.
export interface AuthContextType extends AuthState {
  iniciarSesion: (credenciales: LoginRequest) => Promise<void>
  // HU-26: credencial (ID token) de Google Identity Services.
  iniciarSesionGoogle: (credential: string, opciones?: OpcionesAccesoGoogle) => Promise<string | null>
  registrar: (datos: RegistroRequest) => Promise<void>
  cerrarSesion: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | null>(null)

// HU-26: acceso de estudiantes o de personal (docentes y administrativos) y rol elegido en el primer ingreso.
export interface OpcionesAccesoGoogle {
  portal?: 'estudiantes' | 'personal'
  rol?: string
}
