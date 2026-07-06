// Instancia de Axios configurada para comunicarse con el backend de PseudoTutor.
// Incluye interceptores que:
//   1. Adjuntan automáticamente el Bearer token a cada petición.
//   2. Refrescan el access token cuando el backend responde 401.
//   3. Redirigen a /iniciar-sesion si el refresh falla.

import axios from 'axios'

// Elimina ambos tokens del localStorage.
function limpiarTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// Decodifica el payload del JWT y verifica que no haya expirado.
// Si el token está expirado o malformado, lo limpia del localStorage.
function tokenEsValido(token: string): boolean {
  const partes = token.split('.')
  if (partes.length !== 3) return false
  try {
    const payload = JSON.parse(atob(partes[1]))
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      limpiarTokens()
      return false
    }
    return true
  } catch {
    limpiarTokens()
    return false
  }
}

// Cliente HTTP base. Usa la URL del .env o fallback a localhost:8000.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'X-Content-Type-Options': 'nosniff',
    'X-Requested-With': 'XMLHttpRequest',
  },
})

// Interceptor de REQUEST: si hay un access token válido en localStorage,
// lo adjunta como header Authorization. Si existe pero está expirado, lo limpia.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token && tokenEsValido(token)) {
    config.headers.Authorization = `Bearer ${token}`
  } else if (token) {
    limpiarTokens()
  }
  return config
})

// Interceptor de RESPONSE: si el backend responde 401 (no autorizado),
// intenta refrescar el access token usando el refresh token.
// Si el refresh funciona, reintenta la petición original.
// Si falla, limpia los tokens y redirige al login.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && tokenEsValido(refreshToken)) {
        try {
          const { data } = await axios.post(
            `${api.defaults.baseURL}/usuarios/token/actualizar/`,
            { refresh: refreshToken }
          )
          localStorage.setItem('access_token', data.access)
          if (data.refresh) {
            localStorage.setItem('refresh_token', data.refresh)
          }
          originalRequest.headers.Authorization = `Bearer ${data.access}`
          return api(originalRequest)
        } catch {
          limpiarTokens()
          window.location.href = '/iniciar-sesion'
        }
      } else {
        limpiarTokens()
        window.location.href = '/iniciar-sesion'
      }
    }

    return Promise.reject(error)
  }
)

export default api
