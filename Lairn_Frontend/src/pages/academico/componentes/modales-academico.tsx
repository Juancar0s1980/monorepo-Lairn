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
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Código</label>
                <Input
                  placeholder="ISW-2026"
                  value={ac.formPrograma.codigo}
                  onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, codigo: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Duración (semestres)</label>
                <Input
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
              <label className="text-xs font-medium text-foreground">Nombre</label>
              <Input
                placeholder="Ingeniería de Software y Computación"
                value={ac.formPrograma.nombre}
                onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, nombre: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Modalidad</label>
                <Select
                  value={ac.formPrograma.modalidad}
                  onValueChange={(v) =>
                    ac.setFormPrograma({ ...ac.formPrograma, modalidad: v ?? 'Presencial' })
                  }
                >
                  <SelectTrigger>
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
                <label className="text-xs font-medium text-foreground">Sede</label>
                <Input
                  value={ac.formPrograma.sede}
                  onChange={(e) => ac.setFormPrograma({ ...ac.formPrograma, sede: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Fecha de vigencia (opcional)</label>
              <Input
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
              <label className="text-xs font-medium text-foreground">Número</label>
              <Input
                type="number"
                min={1}
                max={14}
                value={ac.formSemestre.numero}
                onChange={(e) => ac.setFormSemestre({ ...ac.formSemestre, numero: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Nombre (opcional)</label>
              <Input
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
            <DialogDescription>Código único institucional + ubicación en la malla</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Código</label>
                <Input
                  placeholder="ISW-301"
                  value={ac.formAsignatura.codigo}
                  onChange={(e) => ac.setFormAsignatura({ ...ac.formAsignatura, codigo: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Tipo</label>
                <Select
                  value={ac.formAsignatura.tipo}
                  onValueChange={(v) =>
                    ac.setFormAsignatura({
                      ...ac.formAsignatura,
                      tipo: (v ?? 'obligatoria') as AsignaturaMalla['tipo'],
                    })
                  }
                >
                  <SelectTrigger>
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
              <label className="text-xs font-medium text-foreground">Nombre</label>
              <Input
                placeholder="Programación orientada a objetos"
                value={ac.formAsignatura.nombre}
                onChange={(e) => ac.setFormAsignatura({ ...ac.formAsignatura, nombre: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Créditos</label>
                <Input
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
                <label className="text-xs font-medium text-foreground">Horas/sem</label>
                <Input
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
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Semestre</label>
                <Select
                  value={ac.formAsignatura.semestre}
                  onValueChange={(v) => ac.setFormAsignatura({ ...ac.formAsignatura, semestre: v ?? '' })}
                >
                  <SelectTrigger>
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
            <DialogDescription>Creación manual en el programa activo (HU-01.6)</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Nombre</label>
              <Input
                placeholder="Diseño de software"
                value={ac.formCompetencia.nombre}
                onChange={(e) => ac.setFormCompetencia({ ...ac.formCompetencia, nombre: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Tipo</label>
              <Select
                value={ac.formCompetencia.tipo}
                onValueChange={(v) =>
                  ac.setFormCompetencia({
                    ...ac.formCompetencia,
                    tipo: (v === 'transversal' ? 'transversal' : 'especifica') as
                      | 'transversal'
                      | 'especifica',
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="especifica">Específica</SelectItem>
                  <SelectItem value="transversal">Transversal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Descripción (opcional)</label>
              <Textarea
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
              {ac.editandoResultado ? 'Editar resultado (DCE)' : 'Nuevo resultado (DCE)'}
            </DialogTitle>
            <DialogDescription>
              Competencia + asignatura del mismo programa, afirmación en infinitivo
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Competencia</label>
                <Select
                  value={ac.formResultado.competencia}
                  onValueChange={(v) => ac.setFormResultado({ ...ac.formResultado, competencia: v ?? '' })}
                >
                  <SelectTrigger>
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
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Asignatura</label>
                <Select
                  value={ac.formResultado.asignatura}
                  onValueChange={(v) => ac.setFormResultado({ ...ac.formResultado, asignatura: v ?? '' })}
                >
                  <SelectTrigger>
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
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Afirmación (qué se infiere)</label>
              <Textarea
                placeholder="Diseñar componentes de software aplicando patrones..."
                value={ac.formResultado.descripcion}
                onChange={(e) => ac.setFormResultado({ ...ac.formResultado, descripcion: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Evidencia observable</label>
              <Textarea
                placeholder="El estudiante entrega un diagrama y código que..."
                value={ac.formResultado.evidencia_observable}
                onChange={(e) =>
                  ac.setFormResultado({ ...ac.formResultado, evidencia_observable: e.target.value })
                }
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Tarea sugerida</label>
              <Textarea
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
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Semestre referencia</label>
                <Input
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
                <label className="text-xs font-medium text-foreground">Periodo (opcional)</label>
                <Input
                  placeholder="2026-1"
                  value={ac.formMomento.periodo}
                  onChange={(e) => ac.setFormMomento({ ...ac.formMomento, periodo: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Nombre</label>
              <Input
                placeholder="Momento 1 - Cuarto semestre"
                value={ac.formMomento.nombre}
                onChange={(e) => ac.setFormMomento({ ...ac.formMomento, nombre: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Descripción (opcional)</label>
              <Textarea
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
                  onValueChange={(v) => ac.setFormVinculo({ ...ac.formVinculo, resultado: v ?? '' })}
                >
                  <SelectTrigger className="flex-1">
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
