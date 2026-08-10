"""
Generación de un problema visual de opción múltiple (tipo='problema_visual'
en `Pregunta`): un enunciado genérico compartido + varias VARIANTES, cada
una con su propio diagrama y sus propias 4 opciones de respuesta.

El diagrama se dibuja POR CÓDIGO (SVG), no con un modelo de generación de
imágenes. Se probó primero con Hugging Face (FLUX.1-schnell): la geometría
salía bien, pero el texto/etiquetas del diagrama salían ilegibles (los
modelos de difusión no "escriben" texto de verdad, dibujan pixeles que se le
parecen) — inútil para un ejercicio que el estudiante debe poder leer y
resolver. Dibujar por código garantiza que las etiquetas sean exactas y
legibles, porque literalmente las escribimos nosotros.

Groq/el proveedor configurado en `obtener_cliente_ia()` genera, en un solo
llamado, el enunciado genérico + para cada variante: una geometría
estructurada (una ruta de puntos conectados por segmentos, con longitud y
ángulo de giro — el mismo estilo de diagrama de redes de tuberías, circuitos
en serie, etc.) y sus 4 opciones de respuesta. `_generar_svg` dibuja esa
geometría tal cual, así que el diagrama y las opciones de cada variante usan
exactamente los mismos valores.

No hay ningún paso de calificación por IA/visión en este archivo: la
calificación de `problema_visual` es una comparación exacta de índice
(`Entrega.opcion_seleccionada` contra `VarianteProblemaVisual.respuesta_correcta`),
resuelta en la vista, no aquí.
"""

import json
import math

import openai

from backend_lairn.ia_client import obtener_cliente_ia

ANCHO_SVG = 700
ALTO_SVG = 380
MARGEN_SVG = 70
LONGITUD_SEGMENTO_PX = 90


def _generar_texto_variantes(objetivo_texto: str, tema_curso: str, cantidad: int) -> dict:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    mensaje = f"""Eres un diseñador de ejercicios prácticos con diagrama, para un curso
universitario. Puede ser de cualquier carrera (ingeniería, física, mecánica de
fluidos, circuitos, etc.) — usa el vocabulario propio de la disciplina del objetivo,
no asumas que es programación.

Curso: "{tema_curso}"
Objetivo a evaluar: "{objetivo_texto}"

El diagrama de cada variante es SIEMPRE una RUTA: una serie de puntos conectados por
segmentos rectos, cada uno con una longitud y un ángulo de giro respecto al segmento
anterior (igual que una red de tuberías, un circuito en serie, o una trayectoria).
Represéntalo así aunque el problema no sea literalmente de tuberías.

Genera:
1. Un "enunciado" GENÉRICO (una sola vez, compartido por todas las variantes):
   explica el procedimiento/método que el estudiante debe aplicar y las fórmulas
   de apoyo necesarias, SIN valores numéricos concretos (esos van solo en cada
   variante, en su diagrama).
2. Exactamente {cantidad} "variantes" del mismo problema: mismo tipo de diagrama y
   mismo método de solución, pero cada una con valores numéricos propios y
   distintos entre sí (para que cada estudiante reciba una diferente). Para cada
   variante:
   - "puntos": lista de 3 a 6 letras/etiquetas de los puntos de la ruta, en orden
     (ej. ["A", "B", "C", "D"]).
   - "segmentos": lista con longitud len(puntos)-1 — el segmento i conecta
     puntos[i] con puntos[i+1]. Cada segmento es
     {{"longitud": "texto corto, ej. '135 m' o '2.4 Ω'", "giro_grados": numero}}.
     "giro_grados" es cuánto gira respecto a la dirección del segmento anterior
     (0 = sigue recto; usa múltiplos de 45, ej. 45, -45, 90, -90; el primer
     segmento siempre lleva giro_grados=0). Estos valores (longitudes, número de
     segmentos) son los que debes usar para calcular la respuesta correcta —
     no inventes otros después.
   - "opciones": lista de exactamente 4 respuestas posibles (una correcta según
     los valores de esa variante, tres distractores plausibles pero incorrectos —
     no triviales de descartar a simple vista).
   - "respuesta_correcta": índice (0-3) de la opción correcta en "opciones".

Reglas:
- Las 4 opciones de cada variante deben ser distintas entre sí.
- Los distractores deben ser errores plausibles (ej. error de unidades, fórmula
  incompleta), no valores absurdos.
- En español.

Tu única salida debe ser un objeto JSON válido, sin texto adicional:
{{"enunciado": "...", "variantes": [{{"puntos": ["A", "B", "C"], "segmentos": [{{"longitud": "...", "giro_grados": 0}}, {{"longitud": "...", "giro_grados": 45}}], "opciones": ["...", "...", "...", "..."], "respuesta_correcta": 0}}, ...]}}"""

    ultimo_error = None
    for _ in range(3):
        try:
            # El propio proveedor puede rechazar la generación en modo JSON (ej.
            # estructuras anidadas mal formadas) antes de devolver nada que parsear
            # — se trata igual que un JSON inválido: se reintenta.
            respuesta = client.chat.completions.create(
                model=modelo,
                response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}],
                **{kwarg_max_tokens: 4000},
            )
            datos = json.loads(respuesta.choices[0].message.content)
            _validar_texto_variantes(datos, cantidad)
            return datos
        except (json.JSONDecodeError, ValueError, TypeError, openai.APIError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo variantes válidas tras 3 intentos: {ultimo_error}')


def _validar_texto_variantes(datos: dict, cantidad: int) -> None:
    if not isinstance(datos, dict):
        raise ValueError('la respuesta no es un objeto JSON')
    if not str(datos.get('enunciado', '')).strip():
        raise ValueError('falta o viene vacío "enunciado"')

    variantes = datos.get('variantes')
    if not isinstance(variantes, list) or len(variantes) != cantidad:
        raise ValueError(f'se esperaban {cantidad} variantes')

    for v in variantes:
        if not isinstance(v, dict):
            raise ValueError('cada variante debe ser un objeto')

        puntos = v.get('puntos')
        if not isinstance(puntos, list) or not (3 <= len(puntos) <= 6):
            raise ValueError('"puntos" debe ser una lista de 3 a 6 etiquetas')
        if not all(isinstance(p, str) and p.strip() for p in puntos):
            raise ValueError('todas las etiquetas de "puntos" deben ser texto no vacío')

        segmentos = v.get('segmentos')
        if not isinstance(segmentos, list) or len(segmentos) != len(puntos) - 1:
            raise ValueError('"segmentos" debe tener exactamente len(puntos)-1 elementos')
        for seg in segmentos:
            if not isinstance(seg, dict) or not str(seg.get('longitud', '')).strip():
                raise ValueError('cada segmento debe traer "longitud" no vacía')
            if not isinstance(seg.get('giro_grados'), (int, float)):
                raise ValueError('cada segmento debe traer "giro_grados" numérico')

        opciones = v.get('opciones')
        if not isinstance(opciones, list) or len(opciones) != 4:
            raise ValueError('cada variante debe tener exactamente 4 opciones')
        if not all(isinstance(o, str) and o.strip() for o in opciones):
            raise ValueError('todas las opciones deben ser texto no vacío')
        if len(set(opciones)) != 4:
            raise ValueError('las 4 opciones de una variante deben ser distintas entre sí')
        if not isinstance(v.get('respuesta_correcta'), int) or not (0 <= v['respuesta_correcta'] <= 3):
            raise ValueError('"respuesta_correcta" debe ser un entero entre 0 y 3')


def _escapar_xml(texto: str) -> str:
    return (
        str(texto)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def _generar_svg(puntos: list, segmentos: list) -> bytes:
    """
    Dibuja la ruta de puntos/segmentos como un diagrama SVG simple, estilo
    esquema técnico: los dos extremos se dibujan como un depósito/tanque
    (rectángulo), los puntos intermedios como nodos, y cada segmento con su
    etiqueta de longitud en el punto medio.
    """
    x, y = float(MARGEN_SVG), ALTO_SVG / 2
    angulo = 0.0
    coordenadas = [(x, y)]
    for seg in segmentos:
        angulo += seg['giro_grados']
        rad = math.radians(angulo)
        x += LONGITUD_SEGMENTO_PX * math.cos(rad)
        y -= LONGITUD_SEGMENTO_PX * math.sin(rad)
        coordenadas.append((x, y))

    xs = [c[0] for c in coordenadas]
    ys = [c[1] for c in coordenadas]
    ancho_ruta = max(max(xs) - min(xs), 1.0)
    alto_ruta = max(max(ys) - min(ys), 1.0)
    escala = min((ANCHO_SVG - 2 * MARGEN_SVG) / ancho_ruta, (ALTO_SVG - 2 * MARGEN_SVG) / alto_ruta, 1.0)
    centro_x_ruta = (min(xs) + max(xs)) / 2
    centro_y_ruta = (min(ys) + max(ys)) / 2
    coordenadas = [
        (ANCHO_SVG / 2 + (cx - centro_x_ruta) * escala, ALTO_SVG / 2 + (cy - centro_y_ruta) * escala)
        for cx, cy in coordenadas
    ]

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO_SVG}" height="{ALTO_SVG}" '
        f'viewBox="0 0 {ANCHO_SVG} {ALTO_SVG}" font-family="sans-serif">',
        f'<rect width="{ANCHO_SVG}" height="{ALTO_SVG}" fill="#ffffff"/>',
    ]

    for i in range(len(coordenadas) - 1):
        x1, y1 = coordenadas[i]
        x2, y2 = coordenadas[i + 1]
        partes.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#2563eb" stroke-width="3"/>')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        longitud_texto = _escapar_xml(segmentos[i].get('longitud', ''))
        if longitud_texto:
            partes.append(
                f'<text x="{mx:.1f}" y="{my - 10:.1f}" font-size="14" fill="#1e293b" '
                f'text-anchor="middle">{longitud_texto}</text>'
            )

    for i, (cx, cy) in enumerate(coordenadas):
        etiqueta = _escapar_xml(puntos[i]) if i < len(puntos) else ''
        es_extremo = i == 0 or i == len(coordenadas) - 1
        if es_extremo:
            partes.append(
                f'<rect x="{cx - 22:.1f}" y="{cy - 18:.1f}" width="44" height="36" '
                f'fill="#eff6ff" stroke="#1e40af" stroke-width="2"/>'
            )
        else:
            partes.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="#1e40af"/>')
        dy_etiqueta = 34 if es_extremo else 22
        partes.append(
            f'<text x="{cx:.1f}" y="{cy + dy_etiqueta:.1f}" font-size="15" font-weight="bold" '
            f'fill="#0f172a" text-anchor="middle">{etiqueta}</text>'
        )

    partes.append('</svg>')
    return ''.join(partes).encode('utf-8')


def generar_variantes_problema_visual(objetivo_texto: str, tema_curso: str, cantidad: int = 5) -> dict:
    """
    Devuelve {"enunciado": str, "variantes": [{"opciones": [...], "respuesta_correcta": int, "imagen_bytes": bytes}, ...]}.
    `imagen_bytes` es un SVG (no PNG) — quien lo guarde debe usar extensión .svg.
    """
    datos = _generar_texto_variantes(objetivo_texto, tema_curso, cantidad)

    variantes = []
    for v in datos['variantes']:
        variantes.append({
            'opciones': v['opciones'],
            'respuesta_correcta': v['respuesta_correcta'],
            'imagen_bytes': _generar_svg(v['puntos'], v['segmentos']),
        })

    return {'enunciado': datos['enunciado'], 'variantes': variantes}


VARIANTES_POR_PREGUNTA_LIBRE = 3


def _generar_subtemas(enunciado_docente: str, tema_curso: str, cantidad_preguntas: int) -> list:
    """
    Divide la descripción libre del docente en N sub-temas puntuales y
    distintos entre sí, para generar N problemas visuales independientes
    (cada uno con sus propias variantes) en vez de un solo problema repetido.
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    mensaje = f"""Eres un diseñador de laboratorios prácticos con diagrama, para un curso universitario
de cualquier carrera (ingeniería, física, mecánica de fluidos, circuitos, etc.).

Curso: "{tema_curso}"
Descripción del docente de qué laboratorio quiere: "{enunciado_docente}"

Divide esa descripción en exactamente {cantidad_preguntas} sub-temas puntuales y distintos entre sí
(cada uno evaluará un problema con diagrama independiente). Cada sub-tema debe ser una frase corta,
como un objetivo de aprendizaje puntual.

Tu única salida debe ser un objeto JSON válido, sin texto adicional:
{{"subtemas": ["sub-tema 1", "sub-tema 2", ...]}}"""

    ultimo_error = None
    for _ in range(3):
        try:
            respuesta = client.chat.completions.create(
                model=modelo,
                response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}],
                **{kwarg_max_tokens: 800},
            )
            datos = json.loads(respuesta.choices[0].message.content)
            subtemas = datos.get('subtemas') if isinstance(datos, dict) else None
            if not isinstance(subtemas, list) or len(subtemas) != cantidad_preguntas:
                raise ValueError(f'se esperaban {cantidad_preguntas} subtemas')
            if not all(isinstance(s, str) and s.strip() for s in subtemas):
                raise ValueError('todos los subtemas deben ser texto no vacío')
            return subtemas
        except (json.JSONDecodeError, ValueError, TypeError, openai.APIError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo subtemas válidos tras 3 intentos: {ultimo_error}')


def generar_laboratorio_libre_problema_visual(enunciado_docente: str, tema_curso: str, cantidad_preguntas: int = 3) -> dict:
    """
    Genera un laboratorio COMPLETO (título + instrucciones + N problemas
    visuales independientes, cada uno con sus propias variantes) a partir de
    una descripción libre del docente. Primero divide la descripción en N
    sub-temas (`_generar_subtemas`) y luego genera cada problema con
    `generar_variantes_problema_visual` — reutiliza el mismo generador ya
    probado en vez de intentar un único llamado gigante con N problemas.
    """
    cantidad_preguntas = max(1, min(cantidad_preguntas, 8))
    subtemas = _generar_subtemas(enunciado_docente, tema_curso, cantidad_preguntas)

    preguntas = []
    for subtema in subtemas:
        try:
            borrador = generar_variantes_problema_visual(subtema, tema_curso, cantidad=VARIANTES_POR_PREGUNTA_LIBRE)
        except ValueError:
            continue
        preguntas.append({'enunciado': borrador['enunciado'], 'variantes': borrador['variantes']})

    if not preguntas:
        raise ValueError('La IA no pudo generar ningún problema visual para ese laboratorio.')

    titulo = enunciado_docente.strip()[:80] or 'Laboratorio de problemas visuales'
    return {'titulo': titulo, 'instrucciones': '', 'preguntas': preguntas}
