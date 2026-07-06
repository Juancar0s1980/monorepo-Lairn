// Utilidades para decodificar y leer datos del JWT almacenado en localStorage.

export interface PayloadJWT {
  user_id?: number
  email?: string
  rol?: string
  exp?: number
  iat?: number
  [key: string]: unknown
}

// Decodifica el payload de un JWT sin verificar la firma.
// Retorna null si el token está malformado o expirado.
export function decodificarToken(token: string): PayloadJWT | null {
  const partes = token.split('.')
  if (partes.length !== 3) return null

  try {
    const payload: PayloadJWT = JSON.parse(atob(partes[1]))
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return null
    }
    return payload
  } catch {
    return null
  }
}

// Lee el access token de localStorage y retorna el rol del usuario.
// Retorna undefined si no hay token o el token no contiene rol.
export function obtenerRolDelToken(): string | undefined {
  const token = localStorage.getItem('access_token')
  if (!token) return undefined

  const payload = decodificarToken(token)
  return payload?.rol
}
