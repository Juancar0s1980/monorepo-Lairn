"""
Serializer del recurso `TemaEstudio`.

Sirve tanto para la cola de revisión del docente (incluye `estado`) como para
la lista del estudiante (la vista ya filtra por `estado='aprobado'` antes de
serializar). El FK al curso no se expone como campo de escritura: lo asigna
la vista a partir de la URL, igual que `SerializadorObjetivo`.

`laboratorio_practica_id` es de solo lectura: si el docente generó un
laboratorio de práctica ligado a este tema (ver
`apps.campo_estudio.views.docente.vista_generar_laboratorio_tema`), el
frontend lo usa para mostrar el botón "Practicar este tema" en el chat del
estudiante, enlazando al laboratorio ya existente en vez de crear uno nuevo.
"""

from rest_framework import serializers
from apps.campo_estudio.models import TemaEstudio


class SerializadorTemaEstudio(serializers.ModelSerializer):
    laboratorio_practica_id = serializers.SerializerMethodField()

    class Meta:
        model = TemaEstudio
        fields = ['id', 'titulo', 'contenido', 'estado', 'creado_en', 'aprobado_en', 'laboratorio_practica_id']
        read_only_fields = ['id', 'estado', 'creado_en', 'aprobado_en', 'laboratorio_practica_id']

    def get_laboratorio_practica_id(self, tema):
        laboratorio = tema.laboratorios_practica.first()
        return laboratorio.id if laboratorio else None
