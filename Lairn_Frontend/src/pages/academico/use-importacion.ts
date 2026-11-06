// Hook del asistente "Importar información": estado y llamadas del flujo
// fuente → validar → revisar → confirmar → resultado.
//
// Por qué existe aparte de useAcademico: antes la importación era un
// textarea de JSON con un selector "simulacro/real" y nada impedía importar
// en real sin haber revisado. Ahora:
//   - La validación (modo simulacro) es obligatoria y devuelve una `huella`.
//   - La confirmación (modo real) reenvía la huella; si la fuente cambió, el
//     backend responde 409 y no escribe nada.
//   - Toda la seguridad de la URL (SSRF, tamaño, timeouts) vive en el backend;
//     aquí solo se hace una comprobación de forma para orientar al usuario.

import { useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import type { ResumenImportacion } from '@/types/academico'
import { mensajeError } from './academico-utils'

export type ModalidadImportacion = 'url' | 'archivo' | 'pegado'
export type PasoImportacion = 1 | 2 | 3 | 4

const TAMANO_MAXIMO_ARCHIVO = 5 * 1024 * 1024
// La descarga remota puede tardar; el timeout global de Axios es de 15 s.
const TIMEOUT_IMPORTACION = 60000

export function useImportacion(alImportar: () => Promise<void>) {
  const [paso, setPaso] = useState<PasoImportacion>(1)
  const [modalidad, setModalidad] = useState<ModalidadImportacion>('url')
  const [url, setUrl] = useState('')
  const [textoPegado, setTextoPegado] = useState('')
  const [archivo, setArchivo] = useState<{ nombre: string; datos: unknown } | null>(null)
  const [errorFuente, setErrorFuente] = useState('')
  const [validando, setValidando] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const [previa, setPrevia] = useState<ResumenImportacion | null>(null)
  const [resultado, setResultado] = useState<ResumenImportacion | null>(null)

  const elegirModalidad = (m: ModalidadImportacion) => {
    setModalidad(m)
    setErrorFuente('')
    setPaso(2)
  }

  // Lee el .json en el navegador (no se sube el archivo, solo su contenido).
  const leerArchivo = async (f: File | null) => {
    setErrorFuente('')
    setArchivo(null)
    if (!f) return
    if (f.size > TAMANO_MAXIMO_ARCHIVO) {
      setErrorFuente('El archivo supera el máximo de 5 MB.')
      return
    }
    try {
      setArchivo({ nombre: f.name, datos: JSON.parse(await f.text()) })
    } catch {
      setErrorFuente('El archivo no contiene un JSON válido. Revisa que no tenga comas o llaves de más.')
    }
  }

  // Cuerpo de la petición según la modalidad; null si la fuente no es usable.
  const construirPeticion = (): { ruta: string; cuerpo: Record<string, unknown> } | null => {
    if (modalidad === 'url') {
      const valor = url.trim()
      if (!/^https:\/\/[^\s/]+/i.test(valor)) {
        setErrorFuente('Escribe una dirección completa que empiece por https://')
        return null
      }
      return { ruta: '/evaluacion/integracion/importar-url/', cuerpo: { url: valor } }
    }
    if (modalidad === 'archivo') {
      if (!archivo) {
        setErrorFuente('Selecciona un archivo .json válido.')
        return null
      }
      return {
        ruta: '/evaluacion/integracion/importar-json/',
        cuerpo: { datos: archivo.datos, fuente: 'archivo' },
      }
    }
    if (!textoPegado.trim()) {
      setErrorFuente('Pega el contenido JSON.')
      return null
    }
    try {
      return {
        ruta: '/evaluacion/integracion/importar-json/',
        cuerpo: { datos: JSON.parse(textoPegado), fuente: 'pegado' },
      }
    } catch {
      setErrorFuente('El texto no es un JSON válido. Revisa comillas, comas y llaves.')
      return null
    }
  }

  // Paso 2 → 3: valida sin escribir y muestra la vista previa.
  const validar = async () => {
    setErrorFuente('')
    const peticion = construirPeticion()
    if (!peticion) return
    setValidando(true)
    setPrevia(null)
    try {
      const res = await api.post<ResumenImportacion>(
        peticion.ruta,
        { ...peticion.cuerpo, modo: 'simulacro' },
        { timeout: TIMEOUT_IMPORTACION },
      )
      setPrevia(res.data)
      setPaso(3)
    } catch (err: unknown) {
      setErrorFuente(mensajeError(err, 'No se pudo validar la fuente. Revisa tu conexión e inténtalo de nuevo.'))
    } finally {
      setValidando(false)
    }
  }

  // Paso 3 → 4: importa de verdad lo revisado (misma huella).
  const confirmar = async () => {
    if (!previa || confirmando) return
    const peticion = construirPeticion()
    if (!peticion) return
    setConfirmando(true)
    try {
      const res = await api.post<ResumenImportacion>(
        peticion.ruta,
        { ...peticion.cuerpo, modo: 'real', huella: previa.huella },
        { timeout: TIMEOUT_IMPORTACION },
      )
      setResultado(res.data)
      setPaso(4)
      toast.success('Importación completada')
      await alImportar()
    } catch (err: unknown) {
      const estado = (err as { response?: { status?: number } }).response?.status
      toast.error(mensajeError(err, 'No se pudo completar la importación'))
      // 409: la fuente cambió; hay que volver a validar para ver los datos nuevos.
      if (estado === 409) {
        setPrevia(null)
        setPaso(2)
      }
    } finally {
      setConfirmando(false)
    }
  }

  const reiniciar = () => {
    setPaso(1)
    setPrevia(null)
    setResultado(null)
    setErrorFuente('')
    setArchivo(null)
    setTextoPegado('')
    setUrl('')
  }

  return {
    paso, setPaso, modalidad, elegirModalidad,
    url, setUrl, textoPegado, setTextoPegado, archivo, leerArchivo,
    errorFuente, validando, confirmando, previa, resultado,
    validar, confirmar, reiniciar,
  }
}

export type Importacion = ReturnType<typeof useImportacion>
