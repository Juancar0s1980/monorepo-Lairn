// Alta de una cuenta institucional por el Administrador (HU-26).
// Con el acceso solo por Google, el registro público queda cerrado: el Administrador crea la cuenta
// con el correo institucional y el rol, y la persona entra con «Continuar con Google» (sin contraseña).

import { useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, ShieldCheck } from 'lucide-react'
import type { Rol } from '@/types/usuario'

const VACIO = { email: '', first_name: '', second_name: '', first_last_name: '', second_last_name: '', role_id: '' }

export function DialogoNuevaCuenta<T>({
  abierto,
  alCerrar,
  roles,
  alCrear,
}: {
  abierto: boolean
  alCerrar: () => void
  roles: Rol[]
  alCrear: (usuario: T) => void
}) {
  const [datos, setDatos] = useState(VACIO)
  const [errores, setErrores] = useState<Record<string, string>>({})
  const [guardando, setGuardando] = useState(false)
  const cambiar = (campo: keyof typeof VACIO) => (valor: string) => setDatos((d) => ({ ...d, [campo]: valor }))
  const items = roles.map((r) => ({ value: String(r.id), label: r.name }))

  const guardar = async () => {
    setGuardando(true)
    setErrores({})
    try {
      const { data } = await api.post<T>('/usuarios/administracion/usuarios/', { ...datos, role_id: Number(datos.role_id) || null })
      toast.success('Cuenta creada: la persona ya puede ingresar con Google')
      alCrear(data)
      setDatos(VACIO)
      alCerrar()
    } catch (err: unknown) {
      const respuesta = (err as { response?: { data?: Record<string, string[] | string> } }).response?.data ?? {}
      setErrores(Object.fromEntries(Object.entries(respuesta).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
      toast.error('Revisa los datos de la cuenta')
    } finally {
      setGuardando(false)
    }
  }

  const campo = (id: keyof typeof VACIO, etiqueta: string, opciones: { requerido?: boolean; tipo?: string; ph?: string } = {}) => (
    <div className="space-y-1">
      <Label htmlFor={`nc-${id}`}>
        {etiqueta}
        {opciones.requerido && ' *'}
      </Label>
      <Input id={`nc-${id}`} type={opciones.tipo ?? 'text'} value={datos[id]} placeholder={opciones.ph}
        onChange={(e) => cambiar(id)(e.target.value)} aria-invalid={!!errores[id]} />
      {errores[id] && <p className="text-xs text-destructive">{errores[id]}</p>}
    </div>
  )

  return (
    <Dialog open={abierto} onOpenChange={(v) => !v && alCerrar()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nueva cuenta institucional</DialogTitle>
          <DialogDescription>La persona ingresará con su cuenta Google institucional; no se crea contraseña.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {campo('email', 'Correo institucional', { requerido: true, tipo: 'email', ph: 'nombre.apellido@uniautonoma.edu.co' })}
          <div className="grid gap-3 sm:grid-cols-2">
            {campo('first_name', 'Primer nombre', { requerido: true })}
            {campo('second_name', 'Segundo nombre')}
            {campo('first_last_name', 'Primer apellido', { requerido: true })}
            {campo('second_last_name', 'Segundo apellido')}
          </div>
          <div className="space-y-1">
            <Label htmlFor="nc-rol">Rol *</Label>
            <Select value={datos.role_id} onValueChange={(v) => cambiar('role_id')(String(v ?? ''))} items={items}>
              <SelectTrigger id="nc-rol" className="w-full">
                <SelectValue placeholder="Elige el rol" />
              </SelectTrigger>
              <SelectContent>
                {items.map((i) => (
                  <SelectItem key={i.value} value={i.value}>
                    {i.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errores.role_id && <p className="text-xs text-destructive">{errores.role_id}</p>}
          </div>
          <p className="flex items-start gap-1.5 rounded-lg bg-muted p-2.5 text-xs text-muted-foreground">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" aria-hidden />
            Cuando TI desactive la cuenta (o la desactives aquí), la persona ya no podrá ingresar y su sesión abierta se cierra.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={alCerrar} disabled={guardando}>
            Cancelar
          </Button>
          <Button onClick={() => void guardar()} disabled={guardando}>
            {guardando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
            Crear cuenta
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
