import type { Usuario } from './usuario'

// Credenciales enviadas al endpoint POST /usuarios/iniciar-sesion/.
export interface LoginRequest {
  email: string
  password: string
}

// Respuesta del endpoint de login: contiene el access token y el refresh token JWT.
export interface LoginResponse {
  access: string
  refresh: string
}

// Datos enviados al endpoint POST /usuarios/registrar/.
// second_name y second_last_name son opcionales.
export interface RegistroRequest {
  email: string
  password: string
  first_name: string
  second_name?: string
  first_last_name: string
  second_last_name?: string
}

// Estado global de autenticación mantenido en el contexto React.
export interface AuthState {
  usuario: Usuario | null
  estaAutenticado: boolean
  estaCargando: boolean
  rol: string | undefined
}
