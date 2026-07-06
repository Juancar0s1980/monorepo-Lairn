// Gestión de usuarios (solo accesible para Administrador).
// Lista todos los usuarios del sistema, permite reasignar su rol,
// activar/desactivar la cuenta y eliminarla.
// Obtiene los usuarios de GET /usuarios/administracion/usuarios/ y los roles
// disponibles de GET /usuarios/roles/ para poblar el selector de rol.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { useAuth } from '@/context/contexto-auth/use-auth'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Loader2, Search, Trash2, Users } from 'lucide-react'
import { toast } from 'sonner'
import type { Rol } from '@/types/usuario'

// Modelo de usuario tal como lo devuelve el panel de administración.
interface UsuarioAdmin {
  id: number
  first_name: string
  second_name: string
  first_last_name: string
  second_last_name: string
  email: string
  is_active: boolean
  role: Rol
}

// Construye el nombre completo a partir de los cuatro campos de nombre, sin espacios dobles.
function nombreCompleto(usuario: UsuarioAdmin): string {
  return [
    usuario.first_name,
    usuario.second_name,
    usuario.first_last_name,
    usuario.second_last_name,
  ]
    .filter(Boolean)
    .join(' ')
}

export default function PaginaUsuarios() {
  const { usuario: usuarioActual } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [cargando, setCargando] = useState(true)
  const [busqueda, setBusqueda] = useState('')
  const [usuarioAEliminar, setUsuarioAEliminar] = useState<{ id: number; nombre: string } | null>(null)
  const [eliminando, setEliminando] = useState(false)

  // Carga los usuarios y los roles disponibles al montar el componente.
  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [resUsuarios, resRoles] = await Promise.all([
          api.get<UsuarioAdmin[]>('/usuarios/administracion/usuarios/'),
          api.get<Rol[]>('/usuarios/roles/'),
        ])
        setUsuarios(resUsuarios.data)
        setRoles(resRoles.data)
      } catch {
        toast.error('No se pudieron cargar los usuarios')
      } finally {
        setCargando(false)
      }
    }
    cargarDatos()
  }, [])

  // Filtra por nombre o email en el cliente (la lista de usuarios es pequeña).
  const usuariosFiltrados = useMemo(() => {
    const termino = busqueda.trim().toLowerCase()
    if (!termino) return usuarios
    return usuarios.filter(
      (u) =>
        nombreCompleto(u).toLowerCase().includes(termino) ||
        u.email.toLowerCase().includes(termino)
    )
  }, [usuarios, busqueda])

  // Cambia el rol de un usuario.
  const cambiarRol = async (usuarioId: number, roleId: string) => {
    const anterior = usuarios
    setUsuarios((prev) =>
      prev.map((u) =>
        u.id === usuarioId
          ? { ...u, role: roles.find((r) => r.id === Number(roleId)) ?? u.role }
          : u
      )
    )
    try {
      await api.patch(`/usuarios/administracion/usuarios/${usuarioId}/`, {
        role_id: Number(roleId),
      })
      toast.success('Rol actualizado')
    } catch {
      setUsuarios(anterior)
      toast.error('No se pudo actualizar el rol')
    }
  }

  // Activa o desactiva la cuenta de un usuario.
  const cambiarActivo = async (usuarioId: number, activo: boolean) => {
    const anterior = usuarios
    setUsuarios((prev) =>
      prev.map((u) => (u.id === usuarioId ? { ...u, is_active: activo } : u))
    )
    try {
      await api.patch(`/usuarios/administracion/usuarios/${usuarioId}/`, {
        is_active: activo,
      })
      toast.success(activo ? 'Usuario activado' : 'Usuario desactivado')
    } catch {
      setUsuarios(anterior)
      toast.error('No se pudo actualizar el estado del usuario')
    }
  }

  // Elimina la cuenta de un usuario.
  const eliminarUsuario = async () => {
    if (!usuarioAEliminar) return
    setEliminando(true)
    try {
      await api.delete(`/usuarios/administracion/usuarios/${usuarioAEliminar.id}/`)
      setUsuarios((prev) => prev.filter((u) => u.id !== usuarioAEliminar.id))
      toast.success('Usuario eliminado')
      setUsuarioAEliminar(null)
    } catch {
      toast.error('No se pudo eliminar el usuario')
    } finally {
      setEliminando(false)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Usuarios</h2>
          <p className="text-muted-foreground">
            Gestión de usuarios del sistema
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre o email"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {/* Estado vacío */}
      {usuariosFiltrados.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <Users className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No se encontraron usuarios
          </p>
        </div>
      )}

      {/* Tabla de usuarios */}
      {usuariosFiltrados.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Usuario</TableHead>
              <TableHead className="hidden sm:table-cell">Email</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Activo</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {usuariosFiltrados.map((u) => {
              const esUsuarioActual = u.id === usuarioActual?.id
              return (
                <TableRow key={u.id}>
                  <TableCell>
                    <p className="font-medium">{nombreCompleto(u)}</p>
                    <p className="text-xs text-muted-foreground sm:hidden">
                      {u.email}
                    </p>
                    {esUsuarioActual && (
                      <Badge variant="secondary" className="mt-1">
                        Tú
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">
                    {u.email}
                  </TableCell>
                  <TableCell>
                    <Select
                      value={String(u.role.id)}
                      onValueChange={(valor) => valor && cambiarRol(u.id, valor)}
                      disabled={esUsuarioActual}
                    >
                      <SelectTrigger size="sm" className="w-36">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map((rol) => (
                          <SelectItem key={rol.id} value={String(rol.id)}>
                            {rol.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={u.is_active}
                      onCheckedChange={(valor) => cambiarActivo(u.id, valor)}
                      disabled={esUsuarioActual}
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:text-destructive"
                      disabled={esUsuarioActual}
                      onClick={() =>
                        setUsuarioAEliminar({ id: u.id, nombre: nombreCompleto(u) })
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* Diálogo de confirmación para eliminar usuario */}
      <Dialog
        open={!!usuarioAEliminar}
        onOpenChange={(open) => !open && setUsuarioAEliminar(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Eliminar Usuario</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que deseas eliminar a{' '}
              <span className="font-medium text-foreground">
                {usuarioAEliminar?.nombre}
              </span>
              ? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setUsuarioAEliminar(null)}
              disabled={eliminando}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={eliminarUsuario}
              disabled={eliminando}
            >
              {eliminando ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Eliminando...
                </div>
              ) : (
                'Eliminar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
