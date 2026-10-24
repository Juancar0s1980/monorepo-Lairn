// Módulo 1 — Configuración e Información Académica (Administrador y Coordinador;
// el Coordinador no crea/edita programas ni ve la pestaña Importar).
//
// Vista `/academico` con 5 pestañas:
//   1. Programas     — crear / editar / desactivar (borrado lógico HU-01.8)
//   2. Malla         — semestres + asignaturas (crear / editar / eliminar)
//   3. Competencias  — competencias + resultados DCE (crear / editar / eliminar)
//   4. Momentos      — momentos de evaluación + vínculos a RA (CRUD + vincular)
//   5. Importar      — asistente de importación (URL/archivo/pegado) + PDF con IA
//
// Arquitectura: la lógica vive en useAcademico() y cada pestaña/modal es un
// componente en ./componentes. Esta página solo orquesta layout + tabs.
// Reusa la paleta institucional de src/index.css.

import { Link } from 'react-router-dom'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BookOpen, GraduationCap, Landmark, ListChecks, Loader2, RefreshCw } from 'lucide-react'
import { useAcademico } from './use-academico'
import { TabProgramas } from './componentes/tab-programas'
import { TabMalla } from './componentes/tab-malla'
import { TabCompetencias } from './componentes/tab-competencias'
import { TabMomentos } from './componentes/tab-momentos'
import { TabIntegracion } from './componentes/tab-integracion'
import { ModalesAcademico } from './componentes/modales-academico'

export default function PaginaAcademico() {
  const ac = useAcademico()

  if (ac.cargando) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Encabezado del módulo */}
      <div className="relative overflow-hidden rounded-xl border border-border bg-gradient-to-br from-surface-alt to-secondary p-6">
        <div
          className="absolute inset-0 text-primary opacity-[0.05]"
          style={{
            backgroundImage:
              'radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)',
            backgroundSize: '20px 20px',
          }}
        />
        <div className="relative space-y-1">
          <h1 className="font-heading text-2xl tracking-tight text-foreground">
            Configuración Académica
          </h1>
          <p className="text-muted-foreground text-sm">
            Gestiona los programas académicos, su malla curricular, competencias, resultados de
            aprendizaje y momentos de evaluación.{' '}
            {ac.esAdmin
              ? 'Puedes registrarlos uno a uno o importarlos desde el sistema institucional.'
              : 'Los programas los registra la administración; tú organizas su estructura curricular.'}
          </p>
        </div>
      </div>

      {/* Selector de programa activo */}
      <Card>
        <CardHeader className="flex flex-col gap-3 space-y-0 pb-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base">Programa activo</CardTitle>
            <CardDescription>
              Elige el programa para ver su malla, competencias y momentos
            </CardDescription>
          </div>
          <Select
            value={ac.programaId}
            onValueChange={(v) => ac.setProgramaId(v ?? '')}
            items={ac.programas.map((p) => ({ value: String(p.id), label: `${p.codigo} — ${p.nombre}` }))}
          >
            <SelectTrigger className="w-full sm:w-[320px]" aria-label="Programa activo">
              <SelectValue placeholder="Selecciona un programa" />
            </SelectTrigger>
            <SelectContent>
              {ac.programas.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.codigo} — {p.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
      </Card>

      <Tabs defaultValue="programas" className="space-y-4">
        {/* En móvil las pestañas se desplazan horizontalmente en vez de comprimirse */}
        <TabsList
          className={`flex w-full justify-start overflow-x-auto overflow-y-hidden bg-muted sm:grid sm:overflow-visible ${ac.esAdmin ? 'sm:grid-cols-5' : 'sm:grid-cols-4'}`}
        >
          <TabsTrigger value="programas" className="gap-1.5">
            <Landmark className="h-3.5 w-3.5" />
            Programas
          </TabsTrigger>
          <TabsTrigger value="malla" className="gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Malla
          </TabsTrigger>
          <TabsTrigger value="competencias" className="gap-1.5">
            <GraduationCap className="h-3.5 w-3.5" />
            Competencias
          </TabsTrigger>
          <TabsTrigger value="momentos" className="gap-1.5">
            <ListChecks className="h-3.5 w-3.5" />
            Momentos
          </TabsTrigger>
          {/* Importar datos institucionales es exclusivo del Administrador (HU-03) */}
          {ac.esAdmin && (
            <TabsTrigger value="integracion" className="gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" />
              Importar
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="programas" className="space-y-4">
          <TabProgramas ac={ac} />
        </TabsContent>

        <TabsContent value="malla" className="space-y-4">
          <TabMalla ac={ac} />
        </TabsContent>

        <TabsContent value="competencias" className="space-y-4">
          <TabCompetencias ac={ac} />
        </TabsContent>

        <TabsContent value="momentos" className="space-y-4">
          <TabMomentos ac={ac} />
        </TabsContent>

        {ac.esAdmin && (
          <TabsContent value="integracion" className="space-y-4">
            <TabIntegracion ac={ac} />
          </TabsContent>
        )}
      </Tabs>

      <ModalesAcademico ac={ac} />

      {/* Link de navegación auxiliar (el Coordinador no tiene dashboard propio) */}
      {ac.esAdmin && (
        <p className="text-xs text-muted-foreground">
          ¿Volver al inicio?{' '}
          <Link to="/" className="text-primary hover:underline">
            Ir al dashboard
          </Link>
        </p>
      )}
    </div>
  )
}
