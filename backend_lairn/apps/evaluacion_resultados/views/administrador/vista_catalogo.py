"""
Vistas de administración del módulo (solo `Administrador`).

Todas exigen JWT + rol Administrador. La propiedad se valida por URL:
el `programa_id` / `momento_id` viene del path y el objeto se busca
filtrado por ese padre, así el payload no puede reasignar FKs ajenas.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    CargueDocumental,
    Competencia,
    MomentoEvaluacion,
    MomentoResultado,
    OpcionesEstadoCargue,
    OpcionesEstadoRevision,
    ProgramaAcademico,
    ResultadoAprendizaje,
    SemestrePrograma,
)
from apps.evaluacion_resultados.serializers import (
    SerializadorAsignatura,
    SerializadorCompetencia,
    SerializadorMomento,
    SerializadorMomentoResultado,
    SerializadorPrograma,
    SerializadorResultado,
    SerializadorSemestre,
)
from apps.evaluacion_resultados.services.servicio_trazabilidad import (
    requiere_versionado,
    versionar_resultado,
)
from core.permissions.permisos_rol import EsAdministrador


class VistaListaCrearProgramas(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    queryset = ProgramaAcademico.objects.filter(activo=True).prefetch_related('semestres').order_by('nombre')
    serializer_class = SerializadorPrograma

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, origen='manual')


class VistaDetallePrograma(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH actualiza; DELETE = borrado lógico en cascada (HU-01.8).

    Desactivar un programa desactiva también toda su estructura (malla,
    competencias, RA, momentos y vínculos: desaparecen de las listas pero
    conservan su histórico, venga de manual, IA o JSON). Los cargues aún
    no aprobados se eliminan (su propuesta nunca fue dato real); los
    aprobados se conservan como auditoría de lo incorporado.
    """

    permission_classes = [EsAdministrador]
    queryset = ProgramaAcademico.objects.all()
    serializer_class = SerializadorPrograma

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone

        from rest_framework.response import Response

        programa = self.get_object()
        ahora = timezone.now()
        inactivos = {}
        for nombre, qs in [
            ('semestres', SemestrePrograma.objects.filter(programa=programa, activo=True)),
            ('asignaturas', AsignaturaMalla.objects.filter(programa=programa, activo=True)),
            ('competencias', Competencia.objects.filter(programa=programa, activo=True)),
            ('momentos', MomentoEvaluacion.objects.filter(programa=programa, activo=True)),
            ('vinculos', MomentoResultado.objects.filter(momento__programa=programa, activo=True)),
        ]:
            inactivos[nombre] = qs.update(
                activo=False,
                estado_revision=OpcionesEstadoRevision.INACTIVO,
                actualizado_en=ahora,
            )
        inactivos['resultados'] = ResultadoAprendizaje.objects.filter(
            asignatura__programa=programa, activo=True,
        ).update(
            activo=False,
            estado_revision=OpcionesEstadoRevision.INACTIVO,
            actualizado_en=ahora,
        )
        # Cargues pendientes: propuesta nunca incorporada → se eliminan.
        # Aprobados: se conservan (auditoría de lo que ya vive en el programa).
        pendientes = CargueDocumental.objects.filter(programa=programa).exclude(
            estado=OpcionesEstadoCargue.APROBADO,
        )
        cargues_eliminados = pendientes.count()
        pendientes.delete()
        cargues_conservados = CargueDocumental.objects.filter(programa=programa).count()

        programa.activo = False
        programa.estado_revision = OpcionesEstadoRevision.INACTIVO
        programa.save(update_fields=['activo', 'estado_revision', 'actualizado_en'])
        return Response({
            'programa_id': programa.id,
            'desactivados': inactivos,
            'cargues_eliminados': cargues_eliminados,
            'cargues_conservados': cargues_conservados,
        }, status=200)


class VistaListaCrearSemestres(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorSemestre

    def get_queryset(self):
        return SemestrePrograma.objects.filter(
            programa_id=self.kwargs['programa_id'], activo=True,
        ).order_by('numero')

    def perform_create(self, serializer):
        programa = get_object_or_404(ProgramaAcademico, pk=self.kwargs['programa_id'])
        serializer.save(programa=programa, creado_por=self.request.user, origen='manual')


class VistaDetalleSemestre(generics.RetrieveUpdateDestroyAPIView):
    """CRUD completo de semestre (malla). DELETE = borrado lógico HU-01.8."""

    permission_classes = [EsAdministrador]
    serializer_class = SerializadorSemestre

    def get_queryset(self):
        return SemestrePrograma.objects.filter(programa_id=self.kwargs['programa_id'])

    def perform_destroy(self, instance):
        instance.activo = False
        instance.estado_revision = OpcionesEstadoRevision.INACTIVO
        instance.save(update_fields=['activo', 'estado_revision'])


class VistaListaCrearAsignaturas(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorAsignatura

    def get_queryset(self):
        return AsignaturaMalla.objects.filter(
            programa_id=self.kwargs['programa_id'], activo=True,
        ).select_related('semestre').order_by('semestre__numero', 'nombre')

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError as ErrorValidacion

        programa = get_object_or_404(ProgramaAcademico, pk=self.kwargs['programa_id'])
        semestre = serializer.validated_data.get('semestre')
        if semestre is not None and semestre.programa_id != programa.id:
            raise ErrorValidacion(
                {'semestre': 'El semestre debe pertenecer al mismo programa.'}
            )
        serializer.save(programa=programa, creado_por=self.request.user, origen='manual')


class VistaDetalleAsignatura(generics.RetrieveUpdateDestroyAPIView):
    """CRUD completo de asignatura (malla). DELETE = borrado lógico HU-01.8."""

    permission_classes = [EsAdministrador]
    serializer_class = SerializadorAsignatura

    def get_queryset(self):
        return AsignaturaMalla.objects.filter(programa_id=self.kwargs['programa_id'])

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError as ErrorValidacion

        semestre = serializer.validated_data.get('semestre')
        if semestre is not None and semestre.programa_id != self.get_object().programa_id:
            raise ErrorValidacion(
                {'semestre': 'El semestre debe pertenecer al mismo programa.'}
            )
        serializer.save()

    def perform_destroy(self, instance):
        instance.activo = False
        instance.estado_revision = OpcionesEstadoRevision.INACTIVO
        instance.save(update_fields=['activo', 'estado_revision'])


class VistaListaCrearCompetencias(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorCompetencia

    def get_queryset(self):
        return Competencia.objects.filter(
            programa_id=self.kwargs['programa_id'], activo=True,
        ).order_by('tipo', 'nombre')

    def perform_create(self, serializer):
        programa = get_object_or_404(ProgramaAcademico, pk=self.kwargs['programa_id'])
        serializer.save(programa=programa, creado_por=self.request.user, origen='manual')


class VistaDetalleCompetencia(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE. DELETE = borrado lógico (HU-01.8).

    La FK de RA usa PROTECT: no se borra físicamente una competencia
    con resultados activos, por eso el delete desactiva en su lugar.
    """
    permission_classes = [EsAdministrador]
    queryset = Competencia.objects.all()
    serializer_class = SerializadorCompetencia

    def perform_destroy(self, instance):
        instance.activo = False
        instance.estado_revision = OpcionesEstadoRevision.INACTIVO
        instance.save(update_fields=['activo', 'estado_revision'])


class VistaListaCrearResultados(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorResultado

    def get_queryset(self):
        return ResultadoAprendizaje.objects.filter(
            asignatura__programa_id=self.kwargs['programa_id'], activo=True,
        ).select_related('competencia', 'asignatura').order_by('asignatura__nombre', 'id')

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError as ErrorValidacion

        programa_id = int(self.kwargs['programa_id'])
        competencia = serializer.validated_data.get('competencia')
        asignatura = serializer.validated_data.get('asignatura')
        if competencia is not None and competencia.programa_id != programa_id:
            raise ErrorValidacion(
                {'competencia': 'La competencia debe pertenecer al programa de la URL.'}
            )
        if asignatura is not None and asignatura.programa_id != programa_id:
            raise ErrorValidacion(
                {'asignatura': 'La asignatura debe pertenecer al programa de la URL.'}
            )
        serializer.save(creado_por=self.request.user, origen='manual')


class VistaDetalleResultado(generics.RetrieveUpdateDestroyAPIView):
    """PUT con versionado HU-01.8: si ya está comprometido, crea versión nueva.

    DELETE = borrado lógico (activo=False) para conservar histórico.
    """

    permission_classes = [EsAdministrador]
    queryset = ResultadoAprendizaje.objects.all()
    serializer_class = SerializadorResultado

    def perform_update(self, serializer):
        instancia = self.get_object()
        if requiere_versionado(instancia):
            nueva = versionar_resultado(
                instancia,
                nuevos_datos={
                    'competencia_id': serializer.validated_data.get('competencia', instancia.competencia).id
                    if serializer.validated_data.get('competencia') else instancia.competencia_id,
                    'asignatura_id': serializer.validated_data.get('asignatura', instancia.asignatura).id
                    if serializer.validated_data.get('asignatura') else instancia.asignatura_id,
                    'descripcion': serializer.validated_data.get('descripcion', instancia.descripcion),
                    'evidencia_observable': serializer.validated_data.get(
                        'evidencia_observable', instancia.evidencia_observable,
                    ),
                    'tarea_sugerida': serializer.validated_data.get(
                        'tarea_sugerida', instancia.tarea_sugerida,
                    ),
                    'criterios_rubrica': serializer.validated_data.get(
                        'criterios_rubrica', instancia.criterios_rubrica,
                    ),
                },
                creado_por=self.request.user,
            )
            # Guarda la nueva instancia para que `update()` la devuelva
            # en la respuesta (antes devolvía la versión vieja desactivada
            # y el frontend creía que el PATCH no había hecho nada).
            serializer.instance = nueva
        else:
            serializer.save()

    def update(self, request, *args, **kwargs):
        # Responde con la versión vigente (nueva si hubo versionado).
        respuesta = super().update(request, *args, **kwargs)
        instancia = self.get_object()
        # Si se versionó, `serializer.instance` ya es la nueva; si el
        # objeto quedó inactivo, recarga la versión reemplazo.
        if not instancia.activo and instancia.reemplazado_por_id:
            from apps.evaluacion_resultados.models import ResultadoAprendizaje
            nueva = ResultadoAprendizaje.objects.get(pk=instancia.reemplazado_por_id)
            respuesta.data = SerializadorResultado(nueva).data
            respuesta.data['versionado'] = True
        return respuesta

    def perform_destroy(self, instance):
        instance.activo = False
        instance.estado_revision = OpcionesEstadoRevision.INACTIVO
        instance.save(update_fields=['activo', 'estado_revision'])


class VistaListaCrearMomentos(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorMomento

    def get_queryset(self):
        return MomentoEvaluacion.objects.filter(
            programa_id=self.kwargs['programa_id'], activo=True,
        ).prefetch_related('vinculos').order_by('semestre_referencia', 'nombre')

    def perform_create(self, serializer):
        programa = get_object_or_404(ProgramaAcademico, pk=self.kwargs['programa_id'])
        serializer.save(programa=programa, creado_por=self.request.user, origen='manual')


class VistaDetalleMomento(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE. DELETE = borrado lógico (HU-01.8).

    Los vínculos (MomentoResultado) cascanean con el momento, pero
    el borrado lógico los conserva; el tablero solo muestra
    momentos activos.
    """
    permission_classes = [EsAdministrador]
    queryset = MomentoEvaluacion.objects.all()
    serializer_class = SerializadorMomento

    def perform_destroy(self, instance):
        instance.activo = False
        instance.estado_revision = OpcionesEstadoRevision.INACTIVO
        instance.save(update_fields=['activo', 'estado_revision'])


class VistaVincularResultadoMomento(generics.ListCreateAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = SerializadorMomentoResultado

    def get_queryset(self):
        return MomentoResultado.objects.filter(
            momento_id=self.kwargs['momento_id'],
        ).select_related('resultado').order_by('id')

    def perform_create(self, serializer):
        momento = get_object_or_404(MomentoEvaluacion, pk=self.kwargs['momento_id'])
        serializer.save(momento=momento, creado_por=self.request.user, origen='manual')


class VistaDetalleVinculo(generics.RetrieveUpdateDestroyAPIView):
    """Detalle de vínculo Momento-RA: permite editar `obligatorio` o desvincular.

    DELETE borra físicamente el vínculo (no es dato histórico en sí mismo;
    el RA y el momento se conservan).
    """

    permission_classes = [EsAdministrador]
    queryset = MomentoResultado.objects.all()
    serializer_class = SerializadorMomentoResultado
