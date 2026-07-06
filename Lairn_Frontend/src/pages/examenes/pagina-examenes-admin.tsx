// Supervisión global de exámenes (solo accesible para Administrador).
// Lista todos los exámenes del sistema, de cualquier curso y docente,
// para auditar la configuración académica sin depender de cada docente.
// Obtiene los datos de GET /examenes/administracion/examenes/.

import { useEffect, useMemo, useState } from 'react'
import api from '@/services/api'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { FileQuestion, Loader2, Search } from 'lucide-react'
import { toast } from 'sonner'

// Modelo de examen tal como lo devuelve el endpoint de administración.
interface ExamenAdmin {
  id: number
  titulo: string
  tema: string
  modo: 'fijo' | 'maestria'
  num_preguntas: number
  tiempo: number
  creado_en: string
  curso: { id: number; nombre: string; codigo: string }
  docente: { nombre: string; email: string }
}

export default function PaginaExamenesAdmin() {
  const [examenes, setExamenes] = useState<ExamenAdmin[]>([])
  const [cargando, setCargando] = useState(true)
  const [busqueda, setBusqueda] = useState('')

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const { data } = await api.get<ExamenAdmin[]>('/examenes/administracion/examenes/')
        setExamenes(data)
      } catch {
        toast.error('No se pudieron cargar los exámenes')
      } finally {
        setCargando(false)
      }
    }
    cargarDatos()
  }, [])

  // Filtra por título, tema, curso o docente en el cliente.
  const examenesFiltrados = useMemo(() => {
    const termino = busqueda.trim().toLowerCase()
    if (!termino) return examenes
    return examenes.filter(
      (e) =>
        e.titulo.toLowerCase().includes(termino) ||
        e.tema.toLowerCase().includes(termino) ||
        e.curso.nombre.toLowerCase().includes(termino) ||
        e.docente.nombre.toLowerCase().includes(termino)
    )
  }, [examenes, busqueda])

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
          <h2 className="text-2xl font-bold tracking-tight">Exámenes</h2>
          <p className="text-muted-foreground">
            Todos los exámenes creados en el sistema, por curso y docente
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por título, curso o docente"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {/* Estado vacío */}
      {examenesFiltrados.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <FileQuestion className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No se encontraron exámenes
          </p>
        </div>
      )}

      {/* Tabla de exámenes */}
      {examenesFiltrados.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Examen</TableHead>
              <TableHead>Curso</TableHead>
              <TableHead className="hidden md:table-cell">Docente</TableHead>
              <TableHead>Modo</TableHead>
              <TableHead className="hidden sm:table-cell">Preguntas</TableHead>
              <TableHead className="hidden lg:table-cell">Creado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {examenesFiltrados.map((examen) => (
              <TableRow key={examen.id}>
                <TableCell>
                  <p className="font-medium">{examen.titulo}</p>
                  <p className="text-xs text-muted-foreground">{examen.tema}</p>
                </TableCell>
                <TableCell>
                  <p>{examen.curso.nombre}</p>
                  <p className="text-xs text-muted-foreground">{examen.curso.codigo}</p>
                </TableCell>
                <TableCell className="hidden md:table-cell text-muted-foreground">
                  <p>{examen.docente.nombre}</p>
                  <p className="text-xs">{examen.docente.email}</p>
                </TableCell>
                <TableCell>
                  <Badge variant={examen.modo === 'maestria' ? 'default' : 'outline'}>
                    {examen.modo === 'maestria' ? 'Maestría' : 'Fijo'}
                  </Badge>
                </TableCell>
                <TableCell className="hidden sm:table-cell text-muted-foreground">
                  {examen.num_preguntas}
                </TableCell>
                <TableCell className="hidden lg:table-cell text-muted-foreground">
                  {new Date(examen.creado_en).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
