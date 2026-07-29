"""
Contrato de entrada/salida del endpoint "Ejecutar" (equivalente a "Run" en
un juez en línea, solo para preguntas `tipo='codigo'`): el estudiante manda
su código/consulta y recibe el resultado contra los casos de test públicos,
sin que se guarde nada.
"""

from rest_framework import serializers


class SerializadorEjecutarCodigo(serializers.Serializer):
    codigo = serializers.CharField(help_text='Código Python o consulta SQL escrita por el estudiante.')


class SerializadorEnviarRespuesta(serializers.Serializer):
    """Contrato de entrada de 'Enviar' (envío calificado), válido para cualquier tipo de pregunta."""
    respuesta = serializers.CharField(help_text='Código/consulta (tipo=codigo) o texto libre del ensayo (tipo=respuesta_libre).')


class SerializadorResultadoCaso(serializers.Serializer):
    caso_test_id = serializers.IntegerField()
    paso = serializers.BooleanField()
    salida_obtenida = serializers.CharField(allow_blank=True)
    salida_esperada = serializers.CharField(allow_blank=True)
    stderr = serializers.CharField(allow_blank=True)
    timeout = serializers.BooleanField()


class SerializadorResultadoEjecucion(serializers.Serializer):
    casos_publicos_totales = serializers.IntegerField()
    casos_publicos_pasados = serializers.IntegerField()
    resultados = SerializadorResultadoCaso(many=True)
