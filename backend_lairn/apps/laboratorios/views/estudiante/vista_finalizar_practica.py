"""
Vista "Finalizar práctica", para el rol Estudiante.

Expone `POST /laboratorios/laboratorios/<laboratorio_id>/finalizar-practica/`.
Solo aplica a laboratorios que son la práctica de un examen (`Laboratorio.examen`
no nulo, ver `apps.examenes.views.examenes.vista_generar_practica_examen`).

Requiere que el estudiante ya haya terminado la teoría de ese examen (una
`SesionExamen` en estado `completado`, con su `Resultado` ya creado por
`vista_responder.py`) y que haya al menos una entrega por cada pregunta del
laboratorio (`calcular_puntaje_laboratorio` devuelve `None` si falta alguna).

Combina la nota: `nota_teoria` (guardada como snapshot al terminar la teoría)
y `nota_practica` (calculada aquí, misma escala 1.0-5.0 que la teoría) se
combinan según `Examen.peso_practica` (0-100) y el resultado se guarda en
`Resultado.nota` — el mismo campo que ya leen todas las vistas de analítica,
así que no hace falta tocarlas. Se puede llamar más de una vez (recalcula
con las entregas más recientes; no bloquea reintentos dentro del
`max_intentos` del laboratorio).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.services.calculador_nota import calcular_puntaje_laboratorio
from apps.motor_adaptativo.models import SesionExamen


@extend_schema(
    tags=['Laboratorios'],
    summary='Finalizar la práctica de un examen y calcular la nota final combinada',
    request=None,
    parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: OpenApiResponse(description='Desglose de nota_teoria, nota_practica y nota final'),
        400: OpenApiResponse(description='Este laboratorio no es práctica de un examen, faltan preguntas por responder, o aún no terminaste la teoría'),
        403: OpenApiResponse(description='No inscrito en el curso'),
        404: OpenApiResponse(description='Laboratorio no encontrado'),
    },
)
class VistaFinalizarPractica(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.select_related('curso', 'examen').get(id=laboratorio_id)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=laboratorio.curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        examen = laboratorio.examen
        if examen is None:
            return Response(
                {'detalle': 'Este laboratorio no es la práctica de ningún examen.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sesion = (
            SesionExamen.objects.filter(examen=examen, estudiante=request.user, estado='completado')
            .order_by('-intento')
            .select_related('resultado')
            .first()
        )
        if sesion is None or not hasattr(sesion, 'resultado'):
            return Response(
                {'detalle': 'Primero debes terminar la parte de teoría de este examen.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resultado = sesion.resultado

        puntaje_practica = calcular_puntaje_laboratorio(laboratorio, request.user)
        if puntaje_practica is None:
            return Response(
                {'detalle': 'Responde todas las preguntas de la práctica antes de finalizar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Snapshot defensivo: si por algún motivo nota_teoria no quedó guardada
        # (ej. sesión completada antes de que existiera este campo), se usa la
        # nota actual como teoría antes de combinar.
        nota_teoria = resultado.nota_teoria if resultado.nota_teoria is not None else resultado.nota

        nota_practica = round(1.0 + (puntaje_practica / 100) * 4.0, 1)
        peso = examen.peso_practica / 100
        nota_final = round(nota_teoria * (1 - peso) + nota_practica * peso, 1)

        resultado.nota_teoria = nota_teoria
        resultado.nota_practica = nota_practica
        resultado.puntaje_practica = puntaje_practica
        resultado.nota = nota_final
        resultado.save(update_fields=['nota_teoria', 'nota_practica', 'puntaje_practica', 'nota'])

        return Response({
            'nota_teoria': nota_teoria,
            'puntaje_practica': puntaje_practica,
            'nota_practica': nota_practica,
            'peso_practica': examen.peso_practica,
            'nota': nota_final,
        })
