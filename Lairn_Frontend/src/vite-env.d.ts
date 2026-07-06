// Tipos personalizados para las variables de entorno de Vite.
// Todas las variables deben empezar con VITE_ para ser accesibles en el cliente.
// Agregar aquí cada nueva variable del .env para tener autocompletado y type safety.

/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base del backend (ej: http://localhost:8000/api) */
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
