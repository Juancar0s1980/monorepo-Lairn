"""
Agente IA `pensum`: extrae la malla curricular desde el PDF del pensum
descargado de la web institucional.

Entrada: texto plano del PDF (máx 15k chars, recorte defensivo).
Salida: JSON {asignaturas: [{codigo, nombre, creditos, intensidad,
tipo, semestre}], advertencias: [...]}.

La salida queda en `borrador_ia`: el admin la revisa y aprueba antes de
incorporarla (nunca se guarda directo como definitivo si viene de IA).
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia


def extraer_malla_pensum(texto_plan: str, nombre_programa: str) -> dict:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    texto = texto_plan[:15000]

    mensaje = f"""Actúa como experto en diseño curricular universitario colombiano.
Lee el pensum del programa "{nombre_programa}" y extrae su malla por semestres.

Texto del PDF:
---
{texto}
---

Devuelve SOLO JSON válido:
{{"asignaturas": [{{"codigo": "MAT101", "nombre": "...", "creditos": 3,
"intensidad": 4, "tipo": "obligatoria|electiva|optativa|practica",
"semestre": 1}}], "advertencias": ["..."]}}
Reglas: no inventes códigos; si falta un dato usa "" o 0; semestre 1..N;
"tipo" solo uno de los 4 valores; máximo 120 asignaturas."""

    ultimo_error = None
    for _ in range(2):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 4000},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            asignaturas = datos.get('asignaturas')
            if not isinstance(asignaturas, list) or not asignaturas:
                raise ValueError('clave "asignaturas" vacía o inválida')
            return {
                'asignaturas': asignaturas[:120],
                'advertencias': datos.get('advertencias', []),
            }
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e
    raise ValueError(f'La IA no pudo extraer la malla tras 2 intentos: {ultimo_error}')
