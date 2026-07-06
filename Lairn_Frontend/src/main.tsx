// Punto de entrada de la aplicación React.
// Monta el componente raíz <App /> dentro del elemento #root del HTML,
// envuelto en StrictMode para detectar problemas potenciales en desarrollo.

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
