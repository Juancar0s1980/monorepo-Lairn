"""
Agente IA `resolucion`: extrae datos del programa y sus momentos de
evaluación desde la resolución / registro calificado (PDF).

Los momentos dependen de cada carrera (ej. Ing. Software 4-6-8).
Salida: {programa: {codigo, nombre, modalidad, sede, duracion,
vigencia}, momentos: [{semestre, nombre, descripcion}], advertencias}.
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia


def extraer_programa_resolucion(texto_pdf: str) -> dict:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    texto = texto_pdf[:12000]

    mensaje = f"""Actúa como experto en normatividad de educación superior en Colombia.
Lee esta resolución / registro calificado y extrae programa y momentos de evaluación.

Texto:
---
{texto}
---

Devuelve SOLO JSON:
{{"programa": {{"codigo": "", "nombre": "", "modalidad": "Presencial",
"sede": "", "duracion": 8, "vigencia": "2030-12-31"}},
"momentos": [{{"semestre": 4, "nombre": "Momento 1 - Cuarto semestre",
"descripcion": ""}}], "advertencias": []}}
Reglas: momentos = hitos de medición de RAs por semestre (ej. 4,6,8);
si no aparecen, deja lista vacía y avisa en advertencias; no inventes."""

    ultimo_error = None
    for _ in range(2):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 2500},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            if not isinstance(datos.get('programa'), dict):
                raise ValueError('clave "programa" inválida')
            datos.setdefault('momentos', [])
            datos.setdefault('advertencias', [])
            return datos
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e
    raise ValueError(f'La IA no pudo extraer la resolución tras 2 intentos: {ultimo_error}')
