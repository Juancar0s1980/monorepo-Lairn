"""
Vista de carga del plan de aula, para el rol Docente.

Expone `POST /cursos/<curso_id>/plan-aula/`: el docente sube el PDF del plan
de aula del curso (multipart/form-data, campo `archivo`). El texto se
extrae en memoria (`agente_plan_aula.extraer_texto_pdf`), la IA localiza y
transcribe los objetivos de aprendizaje del documento
(`agente_plan_aula.extraer_objetivos_plan_aula`), y cada uno se guarda de
inmediato como `ObjetivoCurso` — a diferencia de `VistaSugerirObjetivos`,
aquí no hay paso de curación: el docente ya aprobó el contenido al elegir
ese PDF.

El archivo nunca se persiste a disco ni se asocia a un `FileField`: solo
existe en memoria durante este request y se descarta al terminar.

Este endpoint es de un solo uso por curso: una vez `plan_aula_cargado` queda
en `True`, un segundo intento responde 400 (evita duplicar objetivos).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso, ObjetivoCurso
from apps.examenes.serializers import SerializadorObjetivo
from apps.examenes.services.agente_plan_aula import extraer_texto_pdf, extraer_objetivos_plan_aula


@extend_schema(
    tags=['Objetivos'],
    summary='Cargar el plan de aula (PDF) y generar los objetivos del curso',
    description=(
        'El docente sube el PDF del plan de aula. La IA extrae los objetivos de '
        'aprendizaje del documento y se guardan directamente como ObjetivoCurso. '
        'El PDF no se conserva. Solo puede hacerse una vez por curso.'
    ),
    request=inline_serializer(name='CargarPlanAula', fields={'archivo': drf_serializers.FileField()}),
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        201: SerializadorObjetivo(many=True),
        400: OpenApiResponse(description='Datos inválidos, archivo no es PDF, PDF sin texto legible, o el curso ya tiene su plan de aula cargado'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
        502: OpenApiResponse(description='La IA no pudo extraer objetivos del plan de aula'),
    },
)
class VistaCargarPlanAula(APIView):
    permission_classes = [EsDocente]
    parser_classes = [MultiPartParser]

    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if curso.plan_aula_cargado:
            return Response(
                {'detalle': 'Este curso ya tiene su plan de aula cargado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        archivo = request.FILES.get('archivo')
        if archivo is None:
            return Response({'detalle': 'Debes adjuntar el PDF del plan de aula.'}, status=status.HTTP_400_BAD_REQUEST)
        if not archivo.name.lower().endswith('.pdf'):
            return Response({'detalle': 'El archivo debe ser un PDF.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            texto = extraer_texto_pdf(archivo)
        except Exception:
            return Response({'detalle': 'No se pudo leer el PDF, ¿el archivo está dañado?'}, status=status.HTTP_400_BAD_REQUEST)

        if not texto:
            return Response(
                {'detalle': 'No se pudo extraer texto del PDF. ¿Es un escaneo de imagen sin texto seleccionable?'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            objetivos_extraidos = extraer_objetivos_plan_aula(texto, curso.nombre)
        except ValueError as e:
            return Response({'detalle': f'No se pudieron extraer objetivos: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        objetivos_creados = [
            ObjetivoCurso(curso=curso, descripcion=descripcion, orden=orden)
            for orden, descripcion in enumerate(objetivos_extraidos)
        ]
        ObjetivoCurso.objects.bulk_create(objetivos_creados)

        curso.plan_aula_cargado = True
        curso.save(update_fields=['plan_aula_cargado'])

        objetivos_guardados = ObjetivoCurso.objects.filter(curso=curso).order_by('orden', 'id')
        return Response(
            SerializadorObjetivo(objetivos_guardados, many=True).data,
            status=status.HTTP_201_CREATED,
        )
