// Editor de código reutilizable (CodeMirror) para preguntas de laboratorio.
// Soporta resaltado de sintaxis de Python, JavaScript, Java, C++/C y SQL, y
// sigue el tema claro/oscuro de la app (observa la clase "dark" en <html>,
// que es como mode-toggle.tsx la controla).

import { useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { sql } from '@codemirror/lang-sql'
import { githubLight, githubDark } from '@uiw/codemirror-theme-github'
import type { Extension } from '@uiw/react-codemirror'
import type { LenguajeCodigo } from '@/types/laboratorio'

function useTemaOscuro(): boolean {
  const [oscuro, setOscuro] = useState(
    () => document.documentElement.classList.contains('dark')
  )

  useEffect(() => {
    const observador = new MutationObserver(() => {
      setOscuro(document.documentElement.classList.contains('dark'))
    })
    observador.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observador.disconnect()
  }, [])

  return oscuro
}

// C y C++ comparten el mismo paquete de resaltado (@codemirror/lang-cpp).
const EXTENSION_POR_LENGUAJE: Record<LenguajeCodigo, () => Extension> = {
  python,
  javascript,
  java,
  cpp,
  c: cpp,
  sql,
}

interface EditorCodigoProps {
  lenguaje: LenguajeCodigo
  valor: string
  onChange: (valor: string) => void
  altura?: string
  soloLectura?: boolean
}

export function EditorCodigo({ lenguaje, valor, onChange, altura = '320px', soloLectura = false }: EditorCodigoProps) {
  const oscuro = useTemaOscuro()
  const extensiones = [EXTENSION_POR_LENGUAJE[lenguaje]()]

  return (
    <CodeMirror
      value={valor}
      height={altura}
      theme={oscuro ? githubDark : githubLight}
      extensions={extensiones}
      onChange={onChange}
      readOnly={soloLectura}
      basicSetup={{ lineNumbers: true, foldGutter: true, autocompletion: true }}
      className="overflow-hidden rounded-lg border border-border text-sm"
    />
  )
}
