// Configuración pública del inicio de sesión (HU-26): si es solo institucional, client_id y dominios.
import { useEffect, useState } from 'react'
import api from '@/services/api'

export interface ConfigAcceso {
  solo_institucional: boolean
  google_client_id: string
  dominios: string[]
}

export function useConfigAcceso() {
  const [config, setConfig] = useState<ConfigAcceso | null>(null)
  useEffect(() => {
    let vigente = true
    api
      .get<ConfigAcceso>('/usuarios/config-acceso/')
      .then((r) => vigente && setConfig(r.data))
      .catch(() => vigente && setConfig({ solo_institucional: false, google_client_id: '', dominios: [] }))
    return () => {
      vigente = false
    }
  }, [])
  return config
}
