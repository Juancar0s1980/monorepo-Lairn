"""
Agente IA `diseno_evidencias`: estructura DCE (Icfes 2018) desde el plan
de aula. Extiende a `agente_plan_aula` que solo devolvía strings.

Salida por RA: {descripcion, competencia_sugerida, tipo_competencia,
evidencia_observable, tarea_sugerida, criterios_rubrica: [{criterio,
niveles, peso}]}.

Garantiza rúbricas que suman 100% (HU-08B.2) y vocabulario de la
disciplina del curso (agnóstico de carrera).
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia


def extraer_diseno_evidencias(texto_plan: str, nombre_curso: str) -> list:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    texto = texto_plan[:12000]

    mensaje = f"""Actúa como experto en Diseño Centrado en Evidencias (Icfes 2018).
Del plan de aula del curso "{nombre_curso}" extrae resultados con estructura DCE.

Texto:
---
{texto}
---

Devuelve SOLO JSON:
{{"resultados": [{{"descripcion": "Aplicar ... (máx 25 palabras, infinitivo)",
"competencia_sugerida": "...", "tipo_competencia": "transversal|especifica",
"evidencia_observable": "Qué conducta/producto lo demuestra",
"tarea_sugerida": "Escenario que pide la evidencia",
"criterios_rubrica": [{{"criterio": "...", "niveles": "bajo/básico/alto",
"peso": 50}}]}}]}}
Reglas: pesos de cada RA suman 100; no inventes contenido fuera del texto;
cubre todo el temario sin redundancia; máximo 30 resultados."""

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
            resultados = datos.get('resultados')
            if not isinstance(resultados, list) or not resultados:
                raise ValueError('clave "resultados" vacía o inválida')
            # Normaliza pesos a 100% por RA (defensa ante IA creativa).
            for ra in resultados:
                criterios = ra.get('criterios_rubrica') or []
                total = sum(int(c.get('peso', 0)) for c in criterios)
                if criterios and total != 100:
                    factor = 100 / total if total else 0
                    acumulado = 0
                    for i, c in enumerate(criterios):
                        c['peso'] = int(round(int(c.get('peso', 0)) * factor)) if i < len(criterios) - 1 else 100 - acumulado
                        acumulado += c['peso']
            return resultados[:30]
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e
    raise ValueError(f'La IA no pudo extraer el diseño DCE tras 2 intentos: {ultimo_error}')
