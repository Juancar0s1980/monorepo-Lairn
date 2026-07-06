// Componente raíz de la aplicación.
// Renderiza el Enrutador, que contiene toda la lógica de rutas,
// autenticación y layout compartido.

import { Enrutador } from '@/app/enrutador'
import { TooltipProvider } from '@/components/ui/tooltip'

export default function App() {
  return (
    <TooltipProvider>
      <Enrutador />
    </TooltipProvider>
  )
}
