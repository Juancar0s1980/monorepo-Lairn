// Constante con los tres roles del sistema (case-sensitive, deben coincidir con el backend).
export const ROLES = {
  ADMIN: 'Administrador',
  DOCENTE: 'Docente',
  ESTUDIANTE: 'Estudiante',
} as const

// Representa un rol asignado a un usuario (viene anidado en el objeto Usuario).
export interface Rol {
  id: number
  name: string
}

// Modelo de usuario tal como lo devuelve el endpoint /usuarios/mis-datos/.
export interface Usuario {
  id: number
  email: string
  first_name: string
  second_name: string
  first_last_name: string
  second_last_name: string
  rol: Rol
  is_active: boolean
}
