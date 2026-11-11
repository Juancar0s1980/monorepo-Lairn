// Configuración pública del inicio de sesión (HU-26): si es solo institucional, client_id, dominios
// y los roles que se pueden pedir en el acceso de personal.
import { useEffect, useState } from 'react'
import api from '@/services/api'

export interface RolPersonal {
  rol: string
  requiere_aprobacion: boolean
}

export interface ConfigAcceso {
  solo_institucional: boolean
  google_client_id: string
  dominios: string[]
  roles_personal: RolPersonal[]
}

// Si el servidor no responde se asume el modo seguro: solo Google institucional.
const POR_DEFECTO: ConfigAcceso = { solo_institucional: true, google_client_id: '', dominios: ['uniautonoma.edu.co'], roles_personal: [] }

export function useConfigAcceso() {
  const [config, setConfig] = useState<ConfigAcceso | null>(null)
  useEffect(() => {
    let vigente = true
    api
      .get<ConfigAcceso>('/usuarios/config-acceso/')
      .then((r) => vigente && setConfig({ ...POR_DEFECTO, ...r.data }))
      .catch(() => vigente && setConfig(POR_DEFECTO))
    return () => {
      vigente = false
    }
  }, [])
  return config
}
