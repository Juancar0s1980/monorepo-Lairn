// Layout compartido para todas las rutas autenticadas.
// Incluye:
//   - Header sticky con logo, navegación por rol, email del usuario,
//     toggle de tema oscuro/claro y botón de cerrar sesión.
//   - Área main que renderiza el contenido hijo (la página actual).
// La navegación se adapta según el rol del usuario (Administrador, Docente, Estudiante).

import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/contexto-auth/use-auth'
import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/mode-toggle'
import type { ReactNode } from 'react'
import { BrainCircuit, LogOut, Menu, User } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet'
import { VisuallyHidden } from '@radix-ui/react-visually-hidden'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { SheetPerfil } from './componentes/sheet-perfil'

// Entrada de navegación. El ítem "destacado" (Saber Pro) se pinta como píldora
// institucional (beige/navy con acento dorado y punto naranja) para resaltar que
// es un módulo propio, distinto de los cursos académicos regulares (HU-16.1).
interface RutaNav {
  label: string
  ruta: string
  destacado?: boolean
}

// Mapa de rutas visibles en la barra de navegación, filtradas por rol.
const rutasPorRol: Record<string, RutaNav[]> = {
  Administrador: [
    { label: 'Início', ruta: '/' },
    { label: 'Usuarios', ruta: '/usuarios' },
    { label: 'Académico', ruta: '/academico' },
    { label: 'Exámenes', ruta: '/examenes' },
    { label: 'Analítica', ruta: '/analitica' },
    { label: 'Redes', ruta: '/redes' },
    { label: 'Moderación', ruta: '/moderacion' },
  ],
  Docente: [
    { label: 'Início', ruta: '/' },
    { label: 'Mis Cursos', ruta: '/mis-cursos' },
    { label: 'Saber Pro', ruta: '/saber-pro', destacado: true },
  ],
  Estudiante: [
    { label: 'Início', ruta: '/' },
    { label: 'Mis Cursos', ruta: '/mis-cursos' },
    { label: 'Saber Pro', ruta: '/saber-pro', destacado: true },
  ],
}

export function Layout({ children }: { children: ReactNode }) {
  const { usuario, cerrarSesion, rol } = useAuth()
  const location = useLocation()
  const [menuAbierto, setMenuAbierto] = useState(false)
  const [perfilAbierto, setPerfilAbierto] = useState(false)

  // Determinar las rutas disponibles según el rol del usuario (fallback: Estudiante).
  const rutas = rutasPorRol[rol || 'Estudiante'] || rutasPorRol['Estudiante']

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-border bg-background">
        <div className="flex h-20 items-center justify-between px-4 md:px-6">
          {/* Logo de la aplicación */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-secondary bg-card shadow-sm">
              <BrainCircuit className="h-4 w-4 text-primary" />
            </div>
            <h1 className="font-heading text-xl text-foreground">
              Pseudo<span className="text-primary">Tutor</span>
            </h1>
          </div>

          {/* Navegación central: cápsula flotante, visible solo en desktop */}
          <nav className="hidden md:flex absolute left-1/2 -translate-x-1/2 items-center gap-7 rounded-full bg-card px-6 py-3.5 shadow-sm">
            {rutas.map((ruta) => {
              const activo = location.pathname === ruta.ruta || (ruta.ruta !== '/' && location.pathname.startsWith(ruta.ruta + '/'))
              if (ruta.destacado) {
                // Ítem destacado (Saber Pro): píldora institucional con punto naranja.
                return (
                  <Link
                    key={ruta.ruta}
                    to={ruta.ruta}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.08em] transition-colors duration-200',
                      activo
                        ? 'bg-[#1e3a5f] text-[#F3EDE1] dark:bg-[#E3C063] dark:text-[#172A45]'
                        : 'bg-[#f3ede1] text-[#1e3a5f] ring-1 ring-[#c89b14]/40 hover:bg-[#ede6d8] dark:bg-[#243A5E] dark:text-[#F5EFE0] dark:ring-[#E3C063]/40 dark:hover:bg-[#1E3351]'
                    )}
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-[#e8740e] dark:bg-[#F29A52]" aria-hidden="true" />
                    {ruta.label}
                  </Link>
                )
              }
              return (
                <Link
                  key={ruta.ruta}
                  to={ruta.ruta}
                  className={`border-b-[1.5px] pb-0.5 text-[11px] font-semibold tracking-[0.09em] uppercase transition-colors duration-200 ${
                    activo
                      ? 'border-accent text-primary'
                      : 'border-transparent text-muted-foreground hover:text-primary'
                  }`}
                >
                  {ruta.label}
                </Link>
              )
            })}
          </nav>

          {/* Controles del lado derecho */}
          <div className="flex items-center gap-2 md:gap-3">
            <button
              onClick={() => setPerfilAbierto(true)}
              className="text-xs font-medium text-muted-foreground hidden sm:inline-block hover:text-foreground transition-colors cursor-pointer"
            >
              {usuario?.email}
            </button>
            <ModeToggle />

            {/* Menú hamburguesa: visible solo en móvil */}
            <Sheet open={menuAbierto} onOpenChange={setMenuAbierto}>
              <SheetTrigger
                render={
                  <Button variant="ghost" size="icon" className="md:hidden text-muted-foreground" />
                }
              >
                <Menu className="h-5 w-5" />
              </SheetTrigger>
              <SheetContent side="right" className="w-64">
                <VisuallyHidden>
                  <SheetTitle>Menú de navegación</SheetTitle>
                </VisuallyHidden>
                <nav className="flex flex-col gap-2 mt-8">
                  {rutas.map((ruta) => {
                    const activo = location.pathname === ruta.ruta || (ruta.ruta !== '/' && location.pathname.startsWith(ruta.ruta + '/'))
                    if (ruta.destacado) {
                      // Ítem destacado (Saber Pro): píldora institucional en el menú móvil.
                      return (
                        <Link
                          key={ruta.ruta}
                          to={ruta.ruta}
                          onClick={() => setMenuAbierto(false)}
                          className={cn(
                            'inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-all',
                            activo
                              ? 'bg-[#1e3a5f] text-[#F3EDE1] dark:bg-[#E3C063] dark:text-[#172A45]'
                              : 'bg-[#f3ede1] text-[#1e3a5f] hover:bg-[#ede6d8] dark:bg-[#243A5E] dark:text-[#F5EFE0] dark:hover:bg-[#1E3351]'
                          )}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-[#e8740e] dark:bg-[#F29A52]" aria-hidden="true" />
                          {ruta.label}
                        </Link>
                      )
                    }
                    return (
                      <Link
                        key={ruta.ruta}
                        to={ruta.ruta}
                        onClick={() => setMenuAbierto(false)}
                        className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                          activo
                            ? 'bg-primary text-primary-foreground'
                            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                        }`}
                      >
                        {ruta.label}
                      </Link>
                    )
                  })}
                  <hr className="my-2 border-border" />
                  <Button
                    variant="ghost"
                    className="justify-start text-muted-foreground hover:text-foreground"
                    onClick={() => {
                      setMenuAbierto(false)
                      setPerfilAbierto(true)
                    }}
                  >
                    <User className="h-4 w-4 mr-2" />
                    Mi Perfil
                  </Button>
                  <span className="px-4 text-xs text-muted-foreground">
                    {usuario?.email}
                  </span>
                  <Button
                    variant="ghost"
                    className="justify-start text-muted-foreground hover:text-destructive"
                    onClick={() => {
                      setMenuAbierto(false)
                      cerrarSesion()
                    }}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Cerrar sesión
                  </Button>
                </nav>
              </SheetContent>
            </Sheet>

            {/* Botón cerrar sesión: visible solo en desktop */}
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:inline-flex text-muted-foreground hover:text-destructive"
              onClick={cerrarSesion}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Área de contenido principal */}
      <main className="flex-1 overflow-auto p-4 md:p-6">
        {children}
      </main>

      {/* Sheet lateral de perfil */}
      <SheetPerfil
        abierto={perfilAbierto}
        onCerrar={() => setPerfilAbierto(false)}
      />
    </div>
  )
}
