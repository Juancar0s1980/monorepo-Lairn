// Modales de crear/editar + vínculos momento->RA + confirmación de borrado.
// Extraídos de pagina-academico.tsx para que la página quede legible.

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Pencil, Plus, Trash2, Unlink } from 'lucide-react'
import type { AsignaturaMalla } from '@/types/academico'
import type { Academico } from '../use-academico'

// Etiquetas visibles de los selectores con valores internos.
const TIPOS_ASIGNATURA = [
  { value: 'obligatoria', label: 'Obligatoria' },
  { value: 'electiva', label: 'Electiva' },
  { value: 'optativa', label: 'Optativa' },
  { value: 'practica', label: 'Práctica / Laboratorio' },
]
const TIPOS_COMPETENCIA = [
  { value: 'especifica', label: 'Específica' },
  { value: 'transversal', label: 'Transversal' },
]

export function ModalesAcademico({ ac }: { ac: Academico }) {
  return (
    <>
      {/* =================== MODAL PROGRAMA =================== */}
      <Dialog open={ac.modalPrograma} onOpenChange={ac.setModalPrograma}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>
              {ac.editandoPrograma ? 'Editar programa' : 'Nuevo programa académico'}
            </DialogTitle>
            <DialogDescription>
              Código único (SNIES o interno), nombre y duración en semestres
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-1" className="text-xs font-medium text-foreground">Código <span className="text-destructive" aria-hidden="true">*</span></label>
                <Input id="campo-academico-1"
                  placeholder="ISW-2026"
                  value={ac.formPrograma.codigo}
                  onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, codigo: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-2" className="text-xs font-medium text-foreground">Duración (semestres) <span className="text-destructive" aria-hidden="true">*</span></label>
                <Input id="campo-academico-2"
                  type="number"
                  min={1}
                  max={14}
                  value={ac.formPrograma.duracion_semestres}
                  onChange={(e) =>
                    ac.setFormPrograma({ ...ac.formPrograma, duracion_semestres: Number(e.target.value) })
                  }
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-3" className="text-xs font-medium text-foreground">Nombre <span className="text-destructive" aria-hidden="true">*</span></label>
              <Input id="campo-academico-3"
                placeholder="Ingeniería de Software y Computación"
                value={ac.formPrograma.nombre}
                onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, nombre: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-4" className="text-xs font-medium text-foreground">Modalidad</label>
                <Select
                  value={ac.formPrograma.modalidad}
                  onValueChange={(v) =>
                    ac.setFormPrograma({ ...ac.formPrograma, modalidad: v ?? 'Presencial' })
                  }
                >
                  <SelectTrigger id="campo-academico-4" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Presencial">Presencial</SelectItem>
                    <SelectItem value="Virtual">Virtual</SelectItem>
                    <SelectItem value="Híbrida">Híbrida</SelectItem>
                    <SelectItem value="Distancia">Distancia</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-5" className="text-xs font-medium text-foreground">Sede</label>
                <Input id="campo-academico-5"
                  value={ac.formPrograma.sede}
                  onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, sede: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-6" className="text-xs font-medium text-foreground">Fecha de vigencia (opcional)</label>
              <Input id="campo-academico-6"
                type="date"
                value={ac.formPrograma.fecha_vigencia}
                onChange={(e) =>
                  ac.setFormPrograma({ ...ac.formPrograma, fecha_vigencia: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalPrograma(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarPrograma} disabled={ac.guardando}>
              {ac.guardando ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : ac.editandoPrograma ? (
                <Pencil className="h-4 w-4 mr-1.5" />
              ) : (
                <Plus className="h-4 w-4 mr-1.5" />
              )}
              {ac.editandoPrograma ? 'Guardar cambios' : 'Crear programa'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL SEMESTRE =================== */}
      <Dialog open={ac.modalSemestre} onOpenChange={ac.setModalSemestre}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>{ac.editandoSemestre ? 'Editar semestre' : 'Nuevo semestre'}</DialogTitle>
            <DialogDescription>Número único dentro del programa + nombre opcional</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-7" className="text-xs font-medium text-foreground">Número <span className="text-destructive" aria-hidden="true">*</span></label>
              <Input id="campo-academico-7"
                type="number"
                min={1}
                max={14}
                value={ac.formSemestre.numero}
                onChange={(e) => ac.setFormSemestre({ ...ac.formSemestre, numero: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-8" className="text-xs font-medium text-foreground">Nombre (opcional)</label>
              <Input id="campo-academico-8"
                placeholder="Cuarto semestre"
                value={ac.formSemestre.nombre}
                onChange={(e) => ac.setFormSemestre({ ...ac.formSemestre, nombre: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalSemestre(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarSemestre} disabled={ac.guardando}>
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              {ac.editandoSemestre ? 'Guardar cambios' : 'Crear semestre'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL ASIGNATURA =================== */}
      <Dialog open={ac.modalAsignatura} onOpenChange={ac.setModalAsignatura}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{ac.editandoAsignatura ? 'Editar asignatura' : 'Nueva asignatura'}</DialogTitle>
            <DialogDescription>
              Registra la asignatura con su código institucional y ubícala en un semestre de la malla.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-9" className="text-xs font-medium text-foreground">Código <span className="text-destructive" aria-hidden="true">*</span></label>
                <Input id="campo-academico-9"
                  placeholder="ISW-301"
                  value={ac.formAsignatura.codigo}
                  onChange={(e) => ac.setFormAsignatura({ ...ac.formAsignatura, codigo: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-10" className="text-xs font-medium text-foreground">Tipo</label>
                <Select
                  value={ac.formAsignatura.tipo}
                  items={TIPOS_ASIGNATURA}
                  onValueChange={(v) =>
                    ac.setFormAsignatura({
                      ...ac.formAsignatura,
                      tipo: (v ?? 'obligatoria') as AsignaturaMalla['tipo'],
                    })
                  }
                >
                  <SelectTrigger id="campo-academico-10" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="obligatoria">Obligatoria</SelectItem>
                    <SelectItem value="electiva">Electiva</SelectItem>
                    <SelectItem value="optativa">Optativa</SelectItem>
                    <SelectItem value="practica">Práctica / Laboratorio</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-11" className="text-xs font-medium text-foreground">Nombre <span className="text-destructive" aria-hidden="true">*</span></label>
              <Input id="campo-academico-11"
                placeholder="Programación orientada a objetos"
                value={ac.formAsignatura.nombre}
                onChange={(e) => ac.setFormAsignatura({ ...ac.formAsignatura, nombre: e.target.value })}
              />
            </div>
            {/* Docente que dicta la asignatura: su curso Lairn queda vinculado y así
                accede al banco de preguntas de esta asignatura (HU-04 / HU-05). */}
            <div className="space-y-1.5">
              <label htmlFor="campo-asignatura-docente" className="text-xs font-medium text-foreground">
                Docente (curso en Lairn)
              </label>
              <Select
                value={ac.formAsignatura.curso_vinculado || 'sin-docente'}
                onValueChange={(v) => ac.setFormAsignatura({ ...ac.formAsignatura, curso_vinculado: v ?? '' })}
                items={[
                  { value: 'sin-docente', label: 'Sin docente asignado' },
                  ...ac.cursosVinculables.map((c) => ({ value: String(c.id), label: `${c.nombre} — ${c.docente}` })),
                ]}
              >
                <SelectTrigger id="campo-asignatura-docente" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sin-docente">Sin docente asignado</SelectItem>
                  {ac.cursosVinculables.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.nombre} — {c.docente} ({c.docente_email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                El docente podrá generar y validar preguntas de esta asignatura en su banco.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-12" className="text-xs font-medium text-foreground">Créditos</label>
                <Input id="campo-academico-12"
                  type="number"
                  min={0}
                  max={20}
                  value={ac.formAsignatura.creditos}
                  onChange={(e) =>
                    ac.setFormAsignatura({ ...ac.formAsignatura, creditos: Number(e.target.value) })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-13" className="text-xs font-medium text-foreground">Horas por semana</label>
                <Input id="campo-academico-13"
                  type="number"
                  min={0}
                  value={ac.formAsignatura.intensidad_horaria}
                  onChange={(e) =>
                    ac.setFormAsignatura({
                      ...ac.formAsignatura,
                      intensidad_horaria: Number(e.target.value),
                    })
                  }
                />
              </div>
              <div className="col-span-2 space-y-1.5 sm:col-span-1">
                <label htmlFor="campo-academico-14" className="text-xs font-medium text-foreground">Semestre</label>
                <Select
                  value={ac.formAsignatura.semestre}
                  items={[
                    { value: 'sin-ubicar', label: 'Sin ubicar' },
                    ...ac.semestres.map((s) => ({
                      value: String(s.id),
                      label: `S${s.numero} — ${s.nombre || `Semestre ${s.numero}`}`,
                    })),
                  ]}
                  onValueChange={(v) => ac.setFormAsignatura({ ...ac.formAsignatura, semestre: v ?? '' })}
                >
                  <SelectTrigger id="campo-academico-14" className="w-full">
                    <SelectValue placeholder="Sin ubicar" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sin-ubicar">Sin ubicar</SelectItem>
                    {ac.semestres.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        S{s.numero} — {s.nombre || `Semestre ${s.numero}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalAsignatura(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarAsignatura} disabled={ac.guardando}>
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              {ac.editandoAsignatura ? 'Guardar cambios' : 'Crear asignatura'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL COMPETENCIA =================== */}
      <Dialog open={ac.modalCompetencia} onOpenChange={ac.setModalCompetencia}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{ac.editandoCompetencia ? 'Editar competencia' : 'Nueva competencia'}</DialogTitle>
            <DialogDescription>
              Habilidad que el programa evalúa. Las transversales aplican a varias asignaturas; las
              específicas, a la disciplina.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-15" className="text-xs font-medium text-foreground">Nombre <span className="text-destructive" aria-hidden="true">*</span></label>
              <Input id="campo-academico-15"
                placeholder="Diseño de software"
                value={ac.formCompetencia.nombre}
                onChange={(e) => ac.setFormCompetencia({ ...ac.formCompetencia, nombre: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-16" className="text-xs font-medium text-foreground">Tipo</label>
              <Select
                value={ac.formCompetencia.tipo}
                items={TIPOS_COMPETENCIA}
                onValueChange={(v) =>
                  ac.setFormCompetencia({
                    ...ac.formCompetencia,
                    tipo: (v === 'transversal' ? 'transversal' : 'especifica') as
                      | 'transversal'
                      | 'especifica',
                  })
                }
              >
                <SelectTrigger id="campo-academico-16" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="especifica">Específica</SelectItem>
                  <SelectItem value="transversal">Transversal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-17" className="text-xs font-medium text-foreground">Descripción (opcional)</label>
              <Textarea id="campo-academico-17"
                placeholder="Describe la competencia..."
                value={ac.formCompetencia.descripcion}
                onChange={(e) => ac.setFormCompetencia({ ...ac.formCompetencia, descripcion: e.target.value })}
                className="min-h-[100px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalCompetencia(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarCompetencia} disabled={ac.guardando}>
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              {ac.editandoCompetencia ? 'Guardar cambios' : 'Crear competencia'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL RESULTADO DCE =================== */}
      <Dialog open={ac.modalResultado} onOpenChange={ac.setModalResultado}>
        <DialogContent className="sm:max-w-[520px]">
          <DialogHeader>
            <DialogTitle>
              {ac.editandoResultado ? 'Editar resultado de aprendizaje' : 'Nuevo resultado de aprendizaje'}
            </DialogTitle>
            <DialogDescription>
              Indica qué debe lograr el estudiante, cómo se evidencia y con qué tarea se comprueba.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-1 gap-3">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-18" className="text-xs font-medium text-foreground">Competencia <span className="text-destructive" aria-hidden="true">*</span></label>
                <Select
                  value={ac.formResultado.competencia}
                  items={ac.competencias.map((c) => ({ value: String(c.id), label: c.nombre }))}
                  onValueChange={(v) => ac.setFormResultado({ ...ac.formResultado, competencia: v ?? '' })}
                >
                  <SelectTrigger id="campo-academico-18" className="w-full">
                    <SelectValue placeholder="Selecciona" />
                  </SelectTrigger>
                  <SelectContent>
                    {ac.competencias.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!ac.competencias.length && (
                  <p className="text-xs text-muted-foreground">
                    Este programa no tiene competencias: crea una primero.
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-19" className="text-xs font-medium text-foreground">Asignatura <span className="text-destructive" aria-hidden="true">*</span></label>
                <Select
                  value={ac.formResultado.asignatura}
                  items={ac.asignaturas.map((a) => ({ value: String(a.id), label: `${a.codigo} — ${a.nombre}` }))}
                  onValueChange={(v) => ac.setFormResultado({ ...ac.formResultado, asignatura: v ?? '' })}
                >
                  <SelectTrigger id="campo-academico-19" className="w-full">
                    <SelectValue placeholder="Selecciona" />
                  </SelectTrigger>
                  <SelectContent>
                    {ac.asignaturas.map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>
                        {a.codigo} — {a.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!ac.asignaturas.length && (
                  <p className="text-xs text-muted-foreground">
                    Este programa no tiene asignaturas: agrégalas en la pestaña Malla.
                  </p>
                )}
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-20" className="text-xs font-medium text-foreground">Afirmación (qué se infiere) <span className="text-destructive" aria-hidden="true">*</span></label>
              <Textarea id="campo-academico-20"
                placeholder="Diseñar componentes de software aplicando patrones..."
                aria-describedby="ayuda-afirmacion"
                value={ac.formResultado.descripcion}
                onChange={(e) => ac.setFormResultado({ ...ac.formResultado, descripcion: e.target.value })}
              />
              <p id="ayuda-afirmacion" className="text-xs text-muted-foreground">
                Escríbela en infinitivo: lo que el estudiante debe ser capaz de hacer.
              </p>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-21" className="text-xs font-medium text-foreground">Evidencia observable</label>
              <Textarea id="campo-academico-21"
                placeholder="El estudiante entrega un diagrama y código que..."
                value={ac.formResultado.evidencia_observable}
                onChange={(e) =>
                  ac.setFormResultado({ ...ac.formResultado, evidencia_observable: e.target.value })
                }
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-22" className="text-xs font-medium text-foreground">Tarea sugerida</label>
              <Textarea id="campo-academico-22"
                placeholder="A partir de un caso, construir..."
                value={ac.formResultado.tarea_sugerida}
                onChange={(e) => ac.setFormResultado({ ...ac.formResultado, tarea_sugerida: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalResultado(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarResultado} disabled={ac.guardando}>
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              {ac.editandoResultado ? 'Guardar cambios' : 'Crear resultado'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL MOMENTO =================== */}
      <Dialog open={ac.modalMomento} onOpenChange={ac.setModalMomento}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{ac.editandoMomento ? 'Editar momento' : 'Nuevo momento'}</DialogTitle>
            <DialogDescription>
              Punto de medición dentro del programa (ej. semestre 4, 6, 8)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-23" className="text-xs font-medium text-foreground">Semestre referencia</label>
                <Input id="campo-academico-23"
                  type="number"
                  min={1}
                  max={14}
                  value={ac.formMomento.semestre_referencia}
                  onChange={(e) =>
                    ac.setFormMomento({ ...ac.formMomento, semestre_referencia: Number(e.target.value) })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="campo-academico-24" className="text-xs font-medium text-foreground">Periodo (opcional)</label>
                <Input id="campo-academico-24"
                  placeholder="2026-1"
                  value={ac.formMomento.periodo}
                  onChange={(e) => ac.setFormMomento({ ...ac.formMomento, periodo: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-25" className="text-xs font-medium text-foreground">Nombre <span className="text-destructive" aria-hidden="true">*</span></label>
              <Input id="campo-academico-25"
                placeholder="Momento 1 - Cuarto semestre"
                value={ac.formMomento.nombre}
                onChange={(e) => ac.setFormMomento({ ...ac.formMomento, nombre: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="campo-academico-26" className="text-xs font-medium text-foreground">Descripción (opcional)</label>
              <Textarea id="campo-academico-26"
                value={ac.formMomento.descripcion}
                onChange={(e) => ac.setFormMomento({ ...ac.formMomento, descripcion: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setModalMomento(false)}>
              Cancelar
            </Button>
            <Button onClick={ac.guardarMomento} disabled={ac.guardando}>
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              {ac.editandoMomento ? 'Guardar cambios' : 'Crear momento'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== MODAL VÍNCULOS =================== */}
      <Dialog
        open={ac.momentoVinculando !== null}
        onOpenChange={(abierto) => {
          if (!abierto) ac.setMomentoVinculando(null)
        }}
      >
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader>
            <DialogTitle>Vincular resultados — {ac.momentoVinculando?.nombre}</DialogTitle>
            <DialogDescription>
              Asocia resultados de aprendizaje al momento y marca si son obligatorios
            </DialogDescription>
          </DialogHeader>
          {ac.cargandoVinculos ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-3 py-2">
              <div className="flex gap-2">
                <Select
                  value={ac.formVinculo.resultado}
                  items={ac.resultados.map((ra) => ({ value: String(ra.id), label: ra.descripcion.slice(0, 70) }))}
                  onValueChange={(v) => ac.setFormVinculo({ ...ac.formVinculo, resultado: v ?? '' })}
                >
                  <SelectTrigger className="min-w-0 flex-1">
                    <SelectValue placeholder="Selecciona un RA para vincular" />
                  </SelectTrigger>
                  <SelectContent>
                    {ac.resultados.map((ra) => (
                      <SelectItem key={ra.id} value={String(ra.id)}>
                        {ra.descripcion.slice(0, 70)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant={ac.formVinculo.obligatorio ? 'default' : 'outline'}
                  onClick={() =>
                    ac.setFormVinculo({ ...ac.formVinculo, obligatorio: !ac.formVinculo.obligatorio })
                  }
                  title="Alternar obligatorio / complementario"
                >
                  {ac.formVinculo.obligatorio ? 'Obligatorio' : 'Complementario'}
                </Button>
                <Button onClick={ac.crearVinculo} disabled={ac.guardando}>
                  {ac.guardando ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>RA vinculado</TableHead>
                    <TableHead>Oblig.</TableHead>
                    <TableHead className="text-right">Quitar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ac.vinculosMomento.map((v) => {
                    const ra = ac.resultados.find((r) => r.id === v.resultado)
                    const descripcion =
                      v.resultado_descripcion ?? ra?.descripcion ?? `RA #${v.resultado}`
                    return (
                      <TableRow key={v.id}>
                        <TableCell className="text-sm">{descripcion}</TableCell>
                        <TableCell>{v.obligatorio ? 'Sí' : 'No'}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              ac.setConfirmacion({
                                tipo: 'vinculo',
                                id: v.id,
                                nombre: descripcion.slice(0, 60),
                              })
                            }
                            title="Desvincular"
                          >
                            <Unlink className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              {!ac.vinculosMomento.length && (
                <p className="text-sm text-muted-foreground">
                  Sin vínculos. Selecciona un RA y pulsa + para asociarlo.
                </p>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setMomentoVinculando(null)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =================== CONFIRMACIÓN DE BORRADO =================== */}
      <Dialog
        open={ac.confirmacion !== null}
        onOpenChange={(abierto) => {
          if (!abierto) ac.setConfirmacion(null)
        }}
      >
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>
              {ac.confirmacion?.tipo === 'programa'
                ? 'Desactivar programa'
                : ac.confirmacion?.tipo === 'cargue'
                  ? 'Eliminar cargue'
                  : `Eliminar ${ac.confirmacion?.tipo}`}
            </DialogTitle>
            <DialogDescription>
              {ac.confirmacion?.tipo === 'vinculo'
                ? 'Se quita la asociación entre el momento y el resultado. Ningún dato histórico se borra.'
                : ac.confirmacion?.tipo === 'cargue'
                  ? 'Se elimina el cargue y su propuesta (el PDF nunca se guardó). Un aprobado solo se puede eliminar si su programa ya no está activo.'
                  : ac.confirmacion?.tipo === 'programa'
                    ? 'Cascada: desactiva malla, competencias, RA y momentos (quedan en histórico) y elimina los cargues aún no aprobados.'
                    : 'Borrado lógico: desaparece de las listas pero conserva su histórico (HU-01.8).'}
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            ¿Confirmar para{' '}
            <span className="font-medium text-foreground">{ac.confirmacion?.nombre}</span>?
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => ac.setConfirmacion(null)}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={ac.ejecutarBorrado} disabled={ac.eliminando}>
              {ac.eliminando ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-1.5" />
              )}
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
