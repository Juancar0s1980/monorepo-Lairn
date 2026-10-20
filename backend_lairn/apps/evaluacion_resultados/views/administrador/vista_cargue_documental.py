"""
Vistas de cargue documental + IA (pensum / resolución / plan de aula).

Seguridad:
  - Solo Administrador.
  - PDF solo en memoria, máx 10 MB, solo `.pdf`, debe traer texto.
  - Anti-reproceso por `hash_texto`: el mismo documento no genera
    duplicados.
  - La IA propone (`borrador_ia`), el humano aprueba en un segundo
    endpoint (`/cargues/<id>/aprobar/`). Nada entra como definitivo
    sin aprobación.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    CargueDocumental,
    Competencia,
    MomentoEvaluacion,
    OpcionesEstadoCargue,
    OpcionesEstadoRevision,
    OpcionesOrigen,
    OpcionesTipoAsignatura,
    OpcionesTipoDocumento,
    ProgramaAcademico,
    ResultadoAprendizaje,
    SemestrePrograma,
)
from apps.evaluacion_resultados.serializers import SerializadorCargue
from apps.evaluacion_resultados.services.agente_diseno_evidencias import (
    extraer_diseno_evidencias,
)
from apps.evaluacion_resultados.services.agente_pensum import extraer_malla_pensum
from apps.evaluacion_resultados.services.agente_resolucion import (
    extraer_programa_resolucion,
)
from apps.evaluacion_resultados.services.extractor_pdf import (
    calcular_hash_texto,
    extraer_texto_pdf,
)
from core.permissions.permisos_rol import EsAdministrador

TAMANO_MAXIMO_PDF = 10 * 1024 * 1024


def _validar_pdf(archivo):
    if archivo is None:
        return 'Debes adjuntar el PDF.'
    if not archivo.name.lower().endswith('.pdf'):
        return 'El archivo debe ser un PDF.'
    if archivo.size and archivo.size > TAMANO_MAXIMO_PDF:
        return 'El PDF supera 10 MB.'
    return None


class VistaListaCargues(generics.ListAPIView):
    permission_classes = [EsAdministrador]
    queryset = CargueDocumental.objects.all()[:100]
    serializer_class = SerializadorCargue


class VistaDetalleCargue(generics.RetrieveUpdateDestroyAPIView):
    """CRUD del cargue documental: ver, actualizar y eliminar.

    - GET: detalle con propuesta IA + programa destino + error si falló.
    - PATCH `{"programa_id": N}`: reasigna el programa destino (corrige
      subidas al programa equivocado). Acepta `null` para dejarlo sin programa.
    - PATCH `{"estado": ...}`: `procesado ↔ rechazado` (descarta o reabre
      la propuesta sin incorporar nada). Si el programa del cargue ya no
      está activo, también se permite `aprobado → rechazado` (anular una
      incorporación cuyo programa se desactivó después).
    - DELETE: borrado físico (el PDF nunca se guardó). Un `aprobado` solo
      se puede borrar si su programa ya no está activo (o no tiene
      programa); con programa activo se bloquea para no romper auditoría.
    - `fallido` es inmutable: exige subir el PDF de nuevo.
    """

    permission_classes = [EsAdministrador]
    queryset = CargueDocumental.objects.all()
    serializer_class = SerializadorCargue

    def _programa_activo(self, cargue) -> bool:
        return bool(cargue.programa_id and cargue.programa and cargue.programa.activo)

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError as ErrorValidacion

        instancia = self.get_object()
        if instancia.estado == OpcionesEstadoCargue.FALLIDO:
            raise ErrorValidacion('Un cargue fallido no se puede editar: sube el PDF de nuevo.')
        datos = self.request.data
        cambios = {}
        if 'programa_id' in datos:
            if instancia.estado == OpcionesEstadoCargue.APROBADO:
                raise ErrorValidacion(
                    'Un cargue aprobado no puede cambiar de programa.'
                )
            if datos.get('programa_id') in (None, ''):
                cambios['programa'] = None
            else:
                programa = ProgramaAcademico.objects.filter(pk=datos['programa_id']).first()
                if programa is None:
                    raise ErrorValidacion({'programa_id': 'El programa no existe.'})
                cambios['programa'] = programa
        if 'estado' in datos:
            nuevo = datos.get('estado')
            permitido = {
                OpcionesEstadoCargue.PROCESADO: (OpcionesEstadoCargue.RECHAZADO,),
                OpcionesEstadoCargue.RECHAZADO: (OpcionesEstadoCargue.PROCESADO,),
            }.get(instancia.estado, ())
            # Anular: si el programa ya no está activo, la incorporación
            # quedó en histórico y el cargue puede pasar a rechazado.
            if (
                instancia.estado == OpcionesEstadoCargue.APROBADO
                and nuevo == OpcionesEstadoCargue.RECHAZADO
                and not self._programa_activo(instancia)
            ):
                permitido = (OpcionesEstadoCargue.RECHAZADO,)
            if nuevo not in permitido:
                raise ErrorValidacion(
                    {'estado': f'No se puede pasar de {instancia.estado} a {nuevo}.'}
                )
            cambios['estado'] = nuevo
        serializer.save(**cambios)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError as ErrorValidacion

        if instance.estado == OpcionesEstadoCargue.APROBADO and self._programa_activo(instance):
            raise ErrorValidacion(
                'Un cargue aprobado no se puede eliminar mientras su programa '
                'siga activo: ya incorporó registros. Desactiva esos registros '
                'en su pestaña o desactiva el programa.'
            )
        instance.delete()


class VistaCargarDocumento(APIView):
    permission_classes = [EsAdministrador]
    parser_classes = [MultiPartParser]

    def post(self, request):
        tipo = request.data.get('tipo')
        programa_id = request.data.get('programa_id')
        archivo = request.FILES.get('archivo')

        if tipo not in dict(OpcionesTipoDocumento.choices):
            return Response({'detalle': 'Tipo inválido: usa pensum, resolucion o plan_aula.'}, status=400)
        error = _validar_pdf(archivo)
        if error:
            return Response({'detalle': error}, status=400)

        programa = None
        if programa_id:
            programa = get_object_or_404(ProgramaAcademico, pk=programa_id)

        try:
            texto = extraer_texto_pdf(archivo)
        except Exception:
            return Response({'detalle': 'No se pudo leer el PDF, ¿está dañado?'}, status=400)
        if not texto:
            return Response(
                {'detalle': 'PDF sin texto seleccionable (¿escaneo?). Sube un PDF con texto.'},
                status=400,
            )
        hash_texto = calcular_hash_texto(texto)
        if CargueDocumental.objects.filter(hash_texto=hash_texto, estado__in=[
            OpcionesEstadoCargue.PROCESADO, OpcionesEstadoCargue.APROBADO,
        ]).exists():
            return Response(
                {'detalle': 'Este documento ya fue procesado antes (hash duplicado).'},
                status=400,
            )

        try:
            if tipo == OpcionesTipoDocumento.PENSUM:
                propuesta = extraer_malla_pensum(texto, programa.nombre if programa else 'Programa')
            elif tipo == OpcionesTipoDocumento.RESOLUCION:
                propuesta = extraer_programa_resolucion(texto)
            else:
                propuesta = {
                    'resultados': extraer_diseno_evidencias(
                        texto, programa.nombre if programa else 'Curso',
                    ),
                }
        except ValueError as e:
            CargueDocumental.objects.create(
                tipo=tipo, nombre_archivo=archivo.name, hash_texto=hash_texto,
                programa=programa, estado=OpcionesEstadoCargue.FALLIDO,
                detalle_error=str(e)[:1000], creado_por=request.user,
            )
            return Response({'detalle': f'La IA no pudo procesarlo: {e}'}, status=502)
        except Exception as e:
            # Errores del proveedor IA (auth, red, timeout, modelo retirado):
            # antes reventaban con 500 genérico y el frontend mostraba
            # "no se pudo subir" sin pista. Ahora quedan como FALLIDO
            # auditado + 502 con causa accionable.
            CargueDocumental.objects.create(
                tipo=tipo, nombre_archivo=archivo.name, hash_texto=hash_texto,
                programa=programa, estado=OpcionesEstadoCargue.FALLIDO,
                detalle_error=f'{type(e).__name__}: {e}'[:1000], creado_por=request.user,
            )
            return Response(
                {'detalle': (
                    f'El proveedor de IA falló ({type(e).__name__}). '
                    'Revisa AI_PROVIDER y la API key en el .env del backend '
                    'y recrea el contenedor web.'
                )},
                status=502,
            )

        cargue = CargueDocumental.objects.create(
            tipo=tipo, nombre_archivo=archivo.name, hash_texto=hash_texto,
            programa=programa, estado=OpcionesEstadoCargue.PROCESADO,
            propuesta_json=propuesta, creado_por=request.user,
        )
        return Response(SerializadorCargue(cargue).data, status=201)


class VistaAprobarCargue(APIView):
    """Revisa e incorpora la propuesta IA como registros `documento_ia`.

    Flujo en 2 pasos (el frontend muestra la propuesta antes de llamar aquí):
    1. Subir PDF → estado `procesado` con `propuesta_json` lista para revisar.
    2. Revisar + aprobar aquí → incorpora según tipo y pasa a `aprobado`.

    Body opcional: `{"programa_id": N, "asignatura_id": M}`.
    - `programa_id` fija/cambia el programa destino (así los cargues
      subidos sin programa también se pueden incorporar).
    - `asignatura_id` es obligatoria solo para `plan_aula`, porque cada
      RA-DCE cuelga de una asignatura (no se puede adivinar desde el PDF).
    """

    permission_classes = [EsAdministrador]

    def post(self, request, cargue_id):
        cargue = get_object_or_404(CargueDocumental, pk=cargue_id)
        if cargue.estado == OpcionesEstadoCargue.APROBADO:
            return Response({'detalle': 'Ya fue aprobado antes.'}, status=400)
        if cargue.estado == OpcionesEstadoCargue.FALLIDO:
            return Response(
                {'detalle': 'El cargue falló (IA o PDF ilegible). Revisa el detalle del error y sube otro PDF.'},
                status=400,
            )

        # Programa destino: el del body manda; si no, el de la subida.
        # Con `crear_programa: true` (solo resolución con código+nombre en la
        # propuesta) se crea el programa desde el PDF en vez de exigir uno.
        programa = cargue.programa
        propuesta = cargue.propuesta_json or {}
        if request.data.get('programa_id'):
            programa = get_object_or_404(ProgramaAcademico, pk=request.data.get('programa_id'))
            if programa.pk != cargue.programa_id:
                cargue.programa = programa
                cargue.save(update_fields=['programa'])
        if programa is None and request.data.get('crear_programa'):
            if cargue.tipo != OpcionesTipoDocumento.RESOLUCION:
                return Response(
                    {'detalle': 'Solo la resolución trae datos para crear el programa.'},
                    status=400,
                )
            info = propuesta.get('programa') or {}
            cod = (info.get('codigo') or '').strip()
            nom = (info.get('nombre') or '').strip()
            if not cod or not nom:
                return Response(
                    {'detalle': 'La propuesta no trae código y nombre de programa.'},
                    status=400,
                )
            vigencia = None
            if info.get('vigencia'):
                try:
                    import datetime
                    vigencia = datetime.date.fromisoformat(str(info['vigencia'])[:10])
                except ValueError:
                    vigencia = None
            try:
                duracion = int(info.get('duracion') or 8)
            except (ValueError, TypeError):
                duracion = 8
            programa, _ = ProgramaAcademico.objects.update_or_create(
                codigo=cod,
                defaults={
                    'nombre': nom[:200],
                    'modalidad': str(info.get('modalidad') or 'Presencial')[:30],
                    'sede': str(info.get('sede') or 'Principal')[:100],
                    'duracion_semestres': min(max(duracion, 1), 14),
                    'fecha_vigencia': vigencia,
                    'origen': OpcionesOrigen.DOCUMENTO_IA,
                    'datos_origen': info,
                    'estado_revision': OpcionesEstadoRevision.APROBADO,
                    'activo': True,
                },
            )
            cargue.programa = programa
            cargue.save(update_fields=['programa'])
        if programa is None:
            return Response(
                {'detalle': 'Elige el programa destino antes de aprobar.'},
                status=400,
            )

        nuevos = {'asignaturas': 0, 'momentos': 0, 'competencias': 0, 'resultados': 0}
        errores: list = []

        if cargue.tipo == OpcionesTipoDocumento.PENSUM:
            # Correcciones del revisor: [{indice, codigo, nombre?, creditos?,
            # intensidad?, tipo?, semestre?}]. Se aplican sobre la propuesta
            # antes de incorporar (así un PDF sin códigos sí entra al programa).
            items = [dict(it) for it in propuesta.get('asignaturas', [])]
            correcciones = request.data.get('correcciones') or []
            if correcciones and not isinstance(correcciones, list):
                return Response(
                    {'detalle': 'correcciones debe ser una lista.'}, status=400,
                )
            for corr in correcciones:
                idx = corr.get('indice')
                if not isinstance(idx, int) or idx < 0 or idx >= len(items):
                    errores.append(f'Corrección con índice inválido ({idx}): se ignora.')
                    continue
                for campo in ('codigo', 'nombre', 'creditos', 'intensidad', 'tipo', 'semestre'):
                    if corr.get(campo) not in (None, ''):
                        items[idx][campo] = corr[campo]
            # Códigos únicos dentro del lote (después de corregir).
            vistos: dict = {}
            saltar: set = set()
            for i, item in enumerate(items):
                cod = str(item.get('codigo') or '').strip()
                if not cod:
                    errores.append(
                        f"Se omite '{item.get('nombre') or '?'}': sin código "
                        '(complétalo en la revisión, el código no se inventa).'
                    )
                    saltar.add(i)
                elif cod.lower() in vistos:
                    errores.append(f'Se omite {cod}: código duplicado en el lote.')
                    saltar.add(i)
                else:
                    vistos[cod.lower()] = i
            # Códigos que ya existen en OTRO programa: no se mueven solos
            # (update_or_create por código los reasignaría sin avisar).
            if vistos:
                for cod_db, pid in AsignaturaMalla.objects.values_list('codigo', 'programa_id'):
                    low = str(cod_db).lower()
                    if low in vistos and pid != programa.id:
                        i = vistos[low]
                        errores.append(
                            f'Se omite {items[i].get("codigo")}: ya existe en otro programa.'
                        )
                        saltar.add(i)
            for i, item in enumerate(items):
                if i in saltar or not item.get('nombre'):
                    continue
                semestre = None
                if item.get('semestre'):
                    try:
                        semestre, _ = SemestrePrograma.objects.get_or_create(
                            programa=programa, numero=int(item['semestre']),
                            defaults={'origen': OpcionesOrigen.DOCUMENTO_IA,
                                      'estado_revision': OpcionesEstadoRevision.APROBADO},
                        )
                    except (ValueError, TypeError):
                        errores.append(f"{item.get('codigo')}: semestre inválido, se deja sin ubicar.")
                tipo_asig = str(item.get('tipo') or 'obligatoria')[:20]
                if tipo_asig not in dict(OpcionesTipoAsignatura.choices):
                    tipo_asig = 'obligatoria'
                try:
                    _, nuevo = AsignaturaMalla.objects.update_or_create(
                        codigo=str(item['codigo']).strip(),
                        defaults={
                            'programa': programa, 'semestre': semestre,
                            'nombre': str(item['nombre'])[:200],
                            'creditos': int(item.get('creditos') or 3),
                            'intensidad_horaria': int(item.get('intensidad') or 0),
                            'tipo': tipo_asig,
                            'origen': OpcionesOrigen.DOCUMENTO_IA,
                            'datos_origen': item,
                            'estado_revision': OpcionesEstadoRevision.APROBADO,
                            'activo': True,
                        },
                    )
                    nuevos['asignaturas'] += 1 if nuevo else 0
                except (ValueError, TypeError) as e:
                    errores.append(f"{item.get('codigo')}: {e}")

        if cargue.tipo == OpcionesTipoDocumento.RESOLUCION:
            for item in propuesta.get('momentos', []):
                if not item.get('semestre') or not item.get('nombre'):
                    continue
                try:
                    numero = int(item['semestre'])
                    # El semestre también estructura la malla para futuras
                    # asignaturas del programa recién creado o existente.
                    SemestrePrograma.objects.get_or_create(
                        programa=programa, numero=numero,
                        defaults={'origen': OpcionesOrigen.DOCUMENTO_IA,
                                  'estado_revision': OpcionesEstadoRevision.APROBADO},
                    )
                    _, nuevo = MomentoEvaluacion.objects.get_or_create(
                        programa=programa,
                        semestre_referencia=numero,
                        nombre=str(item['nombre'])[:200],
                        defaults={
                            'descripcion': str(item.get('descripcion') or ''),
                            'origen': OpcionesOrigen.DOCUMENTO_IA,
                            'datos_origen': item,
                        },
                    )
                    nuevos['momentos'] += 1 if nuevo else 0
                except (ValueError, TypeError) as e:
                    errores.append(f"{item.get('nombre')}: {e}")

        if cargue.tipo == OpcionesTipoDocumento.PLAN_AULA:
            # Cada RA-DCE necesita asignatura: viene en el body (la UI la pide).
            asignatura = None
            if request.data.get('asignatura_id'):
                asignatura = AsignaturaMalla.objects.filter(
                    pk=request.data.get('asignatura_id'),
                    programa=programa, activo=True,
                ).first()
                if asignatura is None:
                    return Response(
                        {'detalle': 'La asignatura debe pertenecer al programa destino.'},
                        status=400,
                    )
            if asignatura is None:
                return Response(
                    {'detalle': 'El plan de aula necesita la asignatura destino (asignatura_id).'},
                    status=400,
                )
            for item in propuesta.get('resultados', []):
                if not (item.get('descripcion') or '').strip():
                    continue
                nombre_comp = (item.get('competencia_sugerida') or 'General').strip()[:200] or 'General'
                tipo_comp = item.get('tipo_competencia')
                if tipo_comp not in ('transversal', 'especifica'):
                    tipo_comp = 'especifica'
                competencia, comp_nueva = Competencia.objects.get_or_create(
                    programa=programa, nombre=nombre_comp, tipo=tipo_comp,
                    defaults={
                        'descripcion': '',
                        'origen': OpcionesOrigen.DOCUMENTO_IA,
                        'datos_origen': {'competencia_sugerida': nombre_comp},
                        'estado_revision': OpcionesEstadoRevision.APROBADO,
                        'activo': True,
                    },
                )
                nuevos['competencias'] += 1 if comp_nueva else 0
                criterios = item.get('criterios_rubrica') or []
                try:
                    total_peso = sum(int(c.get('peso', 0)) for c in criterios)
                    if criterios and total_peso != 100:
                        raise ValueError(
                            f'Los pesos de la rúbrica deben sumar 100, suman {total_peso}.'
                        )
                    ResultadoAprendizaje.objects.create(
                        competencia=competencia, asignatura=asignatura,
                        descripcion=str(item['descripcion']).strip()[:300],
                        evidencia_observable=str(item.get('evidencia_observable') or ''),
                        tarea_sugerida=str(item.get('tarea_sugerida') or ''),
                        criterios_rubrica=criterios,
                        origen=OpcionesOrigen.DOCUMENTO_IA,
                        datos_origen=item,
                        estado_revision=OpcionesEstadoRevision.APROBADO,
                        activo=True,
                        creado_por=request.user,
                    )
                    nuevos['resultados'] += 1
                except (ValueError, TypeError) as e:
                    errores.append(f"RA '{str(item.get('descripcion') or '')[:60]}': {e}")

        cargue.estado = OpcionesEstadoCargue.APROBADO
        cargue.save(update_fields=['estado'])
        return Response({
            'cargue_id': cargue.id,
            'programa_id': programa.id,
            'incorporados': nuevos['asignaturas'] + nuevos['momentos'] + nuevos['resultados'],
            'detalle': nuevos,
            'errores': errores[:10],
        }, status=200)
