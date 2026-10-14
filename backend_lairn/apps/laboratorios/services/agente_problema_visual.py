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
llamado, el "tipo_diagrama" (ver abajo) + el enunciado genérico + para cada
variante: los valores estructurados propios de ese estilo y sus 4 opciones
de respuesta. El renderer SVG correspondiente dibuja esos valores tal cual,
así que el diagrama y las opciones de cada variante usan exactamente los
mismos números.

Tres estilos de diagrama, cada uno con su propio renderer:
  - "ruta" (`_generar_svg_ruta`): una serie de puntos conectados por
    segmentos rectos, con longitud y ángulo de giro — redes de tuberías,
    trayectorias, circuitos en serie genéricos.
  - "circuito" (`_generar_svg_circuito`): circuito eléctrico en serie con
    símbolos reales (batería, resistencia en zigzag, capacitor, interruptor).
  - "fluidos_compuerta" (`_generar_svg_fluidos_compuerta`): tanque con una
    compuerta/orificio lateral y el agua saliendo — mecánica de fluidos,
    hidráulica, caudal, presión hidrostática.
La IA elige cuál de los tres encaja mejor con el objetivo del curso; no hay
selector manual del docente.

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

TIPOS_DIAGRAMA = ('ruta', 'circuito', 'fluidos_compuerta')
TIPOS_ELEMENTO_CIRCUITO = ('bateria', 'resistencia', 'capacitor', 'interruptor')


def _generar_texto_variantes(objetivo_texto: str, tema_curso: str, cantidad: int) -> dict:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    mensaje = f"""Eres un diseñador de ejercicios prácticos con diagrama, para un curso
universitario. Puede ser de cualquier carrera (ingeniería, física, mecánica de
fluidos, circuitos eléctricos, etc.) — usa el vocabulario propio de la disciplina
del objetivo, no asumas que es programación.

Curso: "{tema_curso}"
Objetivo a evaluar: "{objetivo_texto}"

Primero elige el estilo de diagrama que mejor representa este objetivo, entre
exactamente estos tres:
- "ruta": una serie de puntos conectados por segmentos rectos, cada uno con
  longitud y ángulo de giro (sirve para redes de tuberías, trayectorias,
  circuitos en serie genéricos, cualquier cosa que sea "ir de un punto a otro
  por tramos").
- "circuito": un circuito eléctrico en serie con símbolos reales (batería,
  resistencias, capacitores, interruptores) — úsalo para objetivos de
  circuitos eléctricos/electrónicos.
- "fluidos_compuerta": un tanque/reservorio con una compuerta u orificio por
  donde sale agua — úsalo para objetivos de mecánica de fluidos, hidráulica,
  caída libre de líquidos, caudal, presión hidrostática.

Genera:
1. "tipo_diagrama": uno de "ruta", "circuito" o "fluidos_compuerta", el que
   mejor encaje con el objetivo.
2. Un "enunciado" GENÉRICO (una sola vez, compartido por todas las variantes):
   explica el procedimiento/método que el estudiante debe aplicar y las fórmulas
   de apoyo necesarias, SIN valores numéricos concretos (esos van solo en cada
   variante, en su diagrama).
3. Exactamente {cantidad} "variantes" del mismo problema: mismo diagrama y
   mismo método de solución, pero cada una con valores numéricos propios y
   distintos entre sí (para que cada estudiante reciba una diferente).

El contenido de cada variante depende del "tipo_diagrama" elegido:

Si "tipo_diagrama" es "ruta", cada variante trae:
   - "puntos": lista de 3 a 6 letras/etiquetas de los puntos de la ruta, en orden
     (ej. ["A", "B", "C", "D"]).
   - "segmentos": lista con longitud len(puntos)-1 — el segmento i conecta
     puntos[i] con puntos[i+1]. Cada segmento es
     {{"longitud": "texto corto, ej. '135 m' o '2.4 Ω'", "giro_grados": numero}}.
     "giro_grados" es cuánto gira respecto a la dirección del segmento anterior
     (0 = sigue recto; usa múltiplos de 45, ej. 45, -45, 90, -90; el primer
     segmento siempre lleva giro_grados=0).

Si "tipo_diagrama" es "circuito", cada variante trae:
   - "elementos": lista de 3 a 6 componentes del circuito, EN ORDEN alrededor
     del lazo, con EXACTAMENTE un elemento de tipo "bateria" (la fuente). Cada
     elemento es {{"tipo": "bateria"|"resistencia"|"capacitor"|"interruptor",
     "etiqueta": "texto corto con el valor, ej. '12 V', 'R1 = 220 Ω', '10 µF'"}}.

Si "tipo_diagrama" es "fluidos_compuerta", cada variante trae:
   - "nivel_agua": texto corto con la altura total de la columna de agua en
     el tanque, ej. "H = 5 m".
   - "profundidad_compuerta": texto corto con la profundidad de la compuerta
     respecto a la superficie del agua (el dato que de verdad se usa para
     calcular la velocidad de salida), ej. "h = 1.5 m".
   - "dato_compuerta": texto corto con el dato propio de la compuerta/orificio
     (área, ancho o coeficiente de descarga), ej. "A = 0.3 m²".

En CUALQUIER tipo_diagrama, cada variante también trae:
   - "opciones": lista de exactamente 4 respuestas posibles (una correcta según
     los valores de esa variante, tres distractores plausibles pero incorrectos —
     no triviales de descartar a simple vista).
   - "respuesta_correcta": índice (0-3) de la opción correcta en "opciones".

Estos valores numéricos son los que debes usar para calcular la respuesta
correcta — no inventes otros después.

Reglas:
- Las 4 opciones de cada variante deben ser distintas entre sí.
- Los distractores deben ser errores plausibles (ej. error de unidades, fórmula
  incompleta), no valores absurdos.
- Todas las variantes de un mismo problema usan el MISMO tipo_diagrama.
- En español.

Tu única salida debe ser un objeto JSON válido, sin texto adicional. Ejemplos de
forma según tipo_diagrama:
{{"tipo_diagrama": "ruta", "enunciado": "...", "variantes": [{{"puntos": ["A", "B", "C"], "segmentos": [{{"longitud": "...", "giro_grados": 0}}, {{"longitud": "...", "giro_grados": 45}}], "opciones": ["...", "...", "...", "..."], "respuesta_correcta": 0}}]}}
{{"tipo_diagrama": "circuito", "enunciado": "...", "variantes": [{{"elementos": [{{"tipo": "bateria", "etiqueta": "12 V"}}, {{"tipo": "resistencia", "etiqueta": "R1 = 100 Ω"}}], "opciones": ["...", "...", "...", "..."], "respuesta_correcta": 0}}]}}
{{"tipo_diagrama": "fluidos_compuerta", "enunciado": "...", "variantes": [{{"nivel_agua": "H = 5 m", "profundidad_compuerta": "h = 1.5 m", "dato_compuerta": "A = 0.3 m²", "opciones": ["...", "...", "...", "..."], "respuesta_correcta": 0}}]}}"""

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

    tipo_diagrama = datos.get('tipo_diagrama')
    if tipo_diagrama not in TIPOS_DIAGRAMA:
        raise ValueError(f'"tipo_diagrama" debe ser uno de {TIPOS_DIAGRAMA}')

    variantes = datos.get('variantes')
    if not isinstance(variantes, list) or len(variantes) != cantidad:
        raise ValueError(f'se esperaban {cantidad} variantes')

    validador_por_tipo = {
        'ruta': _validar_variante_ruta,
        'circuito': _validar_variante_circuito,
        'fluidos_compuerta': _validar_variante_fluidos,
    }

    for v in variantes:
        if not isinstance(v, dict):
            raise ValueError('cada variante debe ser un objeto')

        validador_por_tipo[tipo_diagrama](v)

        opciones = v.get('opciones')
        if not isinstance(opciones, list) or len(opciones) != 4:
            raise ValueError('cada variante debe tener exactamente 4 opciones')
        if not all(isinstance(o, str) and o.strip() for o in opciones):
            raise ValueError('todas las opciones deben ser texto no vacío')
        if len(set(opciones)) != 4:
            raise ValueError('las 4 opciones de una variante deben ser distintas entre sí')
        if not isinstance(v.get('respuesta_correcta'), int) or not (0 <= v['respuesta_correcta'] <= 3):
            raise ValueError('"respuesta_correcta" debe ser un entero entre 0 y 3')


def _validar_variante_ruta(v: dict) -> None:
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


def _validar_variante_circuito(v: dict) -> None:
    elementos = v.get('elementos')
    if not isinstance(elementos, list) or not (3 <= len(elementos) <= 6):
        raise ValueError('"elementos" debe ser una lista de 3 a 6 componentes')

    baterias = 0
    for el in elementos:
        if not isinstance(el, dict) or el.get('tipo') not in TIPOS_ELEMENTO_CIRCUITO:
            raise ValueError(f'cada elemento debe traer "tipo" en {TIPOS_ELEMENTO_CIRCUITO}')
        if not str(el.get('etiqueta', '')).strip():
            raise ValueError('cada elemento debe traer "etiqueta" no vacía')
        if el['tipo'] == 'bateria':
            baterias += 1
    if baterias != 1:
        raise ValueError('el circuito debe tener exactamente un elemento "bateria"')


def _validar_variante_fluidos(v: dict) -> None:
    for campo in ('nivel_agua', 'profundidad_compuerta', 'dato_compuerta'):
        if not str(v.get(campo, '')).strip():
            raise ValueError(f'falta o viene vacío "{campo}"')


def _escapar_xml(texto: str) -> str:
    return (
        str(texto)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def _generar_svg_ruta(puntos: list, segmentos: list) -> bytes:
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


def _dibujar_elemento_circuito(partes: list, elemento: dict, cx: float, y: float, hueco: float) -> None:
    """Dibuja el símbolo de un componente de circuito (no batería) centrado en (cx, y), interrumpiendo el cable en ese punto."""
    tipo = elemento['tipo']
    etiqueta = _escapar_xml(elemento['etiqueta'])

    if tipo == 'resistencia':
        n_picos = 5
        ancho_zz = hueco * 2
        x0 = cx - hueco
        puntos_zz = []
        for i in range(n_picos + 1):
            x = x0 + ancho_zz * i / n_picos
            if i == 0 or i == n_picos:
                y_pico = y
            else:
                y_pico = y - 9 if i % 2 else y + 9
            puntos_zz.append(f'{x:.1f},{y_pico:.1f}')
        partes.append(f'<polyline points="{" ".join(puntos_zz)}" fill="none" stroke="#1e293b" stroke-width="2.5"/>')
    elif tipo == 'capacitor':
        partes.append(f'<line x1="{cx - 6:.1f}" y1="{y - 14:.1f}" x2="{cx - 6:.1f}" y2="{y + 14:.1f}" stroke="#1e293b" stroke-width="3"/>')
        partes.append(f'<line x1="{cx + 6:.1f}" y1="{y - 14:.1f}" x2="{cx + 6:.1f}" y2="{y + 14:.1f}" stroke="#1e293b" stroke-width="3"/>')
        partes.append(f'<line x1="{cx - hueco:.1f}" y1="{y:.1f}" x2="{cx - 6:.1f}" y2="{y:.1f}" stroke="#2563eb" stroke-width="3"/>')
        partes.append(f'<line x1="{cx + 6:.1f}" y1="{y:.1f}" x2="{cx + hueco:.1f}" y2="{y:.1f}" stroke="#2563eb" stroke-width="3"/>')
    elif tipo == 'interruptor':
        partes.append(f'<circle cx="{cx - hueco:.1f}" cy="{y:.1f}" r="3" fill="#1e293b"/>')
        partes.append(f'<circle cx="{cx + hueco:.1f}" cy="{y:.1f}" r="3" fill="#1e293b"/>')
        partes.append(
            f'<line x1="{cx - hueco:.1f}" y1="{y:.1f}" x2="{cx + hueco - 8:.1f}" y2="{y - 16:.1f}" '
            f'stroke="#1e293b" stroke-width="2.5"/>'
        )
    else:
        partes.append(f'<line x1="{cx - hueco:.1f}" y1="{y:.1f}" x2="{cx + hueco:.1f}" y2="{y:.1f}" stroke="#2563eb" stroke-width="3"/>')

    partes.append(f'<text x="{cx:.1f}" y="{y - hueco - 10:.1f}" font-size="13" fill="#1e293b" text-anchor="middle">{etiqueta}</text>')


def _generar_svg_circuito(elementos: list) -> bytes:
    """
    Dibuja un circuito en serie como un lazo rectangular: la batería va
    siempre en el lado izquierdo (fuente), y el resto de los elementos se
    reparten en orden a lo largo del lado superior. Lados derecho e inferior
    son cable simple que cierra el lazo.
    """
    x_izq, x_der = float(MARGEN_SVG), float(ANCHO_SVG - MARGEN_SVG)
    y_arriba, y_abajo = float(MARGEN_SVG), float(ALTO_SVG - MARGEN_SVG)
    y_medio = (y_arriba + y_abajo) / 2

    bateria = next(e for e in elementos if e['tipo'] == 'bateria')
    resto = [e for e in elementos if e['tipo'] != 'bateria']

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO_SVG}" height="{ALTO_SVG}" '
        f'viewBox="0 0 {ANCHO_SVG} {ALTO_SVG}" font-family="sans-serif">',
        f'<rect width="{ANCHO_SVG}" height="{ALTO_SVG}" fill="#ffffff"/>',
    ]

    # Lado izquierdo, con un hueco en el medio para el símbolo de batería.
    hueco_bateria = 16
    partes.append(f'<line x1="{x_izq:.1f}" y1="{y_arriba:.1f}" x2="{x_izq:.1f}" y2="{y_medio - hueco_bateria:.1f}" stroke="#2563eb" stroke-width="3"/>')
    partes.append(f'<line x1="{x_izq:.1f}" y1="{y_medio + hueco_bateria:.1f}" x2="{x_izq:.1f}" y2="{y_abajo:.1f}" stroke="#2563eb" stroke-width="3"/>')
    partes.append(f'<line x1="{x_izq - 16:.1f}" y1="{y_medio - hueco_bateria:.1f}" x2="{x_izq + 16:.1f}" y2="{y_medio - hueco_bateria:.1f}" stroke="#1e293b" stroke-width="3"/>')
    partes.append(f'<line x1="{x_izq - 9:.1f}" y1="{y_medio + hueco_bateria:.1f}" x2="{x_izq + 9:.1f}" y2="{y_medio + hueco_bateria:.1f}" stroke="#1e293b" stroke-width="6"/>')
    partes.append(
        f'<text x="{x_izq - 26:.1f}" y="{y_medio + 4:.1f}" font-size="13" fill="#1e293b" '
        f'text-anchor="end">{_escapar_xml(bateria["etiqueta"])}</text>'
    )

    # Lado derecho y lado inferior: cable simple, cierran el lazo.
    partes.append(f'<line x1="{x_der:.1f}" y1="{y_arriba:.1f}" x2="{x_der:.1f}" y2="{y_abajo:.1f}" stroke="#2563eb" stroke-width="3"/>')
    partes.append(f'<line x1="{x_izq:.1f}" y1="{y_abajo:.1f}" x2="{x_der:.1f}" y2="{y_abajo:.1f}" stroke="#2563eb" stroke-width="3"/>')

    # Lado superior: el resto de los elementos, repartidos en orden, con huecos para cada símbolo.
    n = len(resto)
    ancho_disp = x_der - x_izq
    hueco_top = 22
    x_prev = x_izq
    for i, el in enumerate(resto):
        cx = x_izq + ancho_disp * (i + 1) / (n + 1)
        partes.append(f'<line x1="{x_prev:.1f}" y1="{y_arriba:.1f}" x2="{cx - hueco_top:.1f}" y2="{y_arriba:.1f}" stroke="#2563eb" stroke-width="3"/>')
        _dibujar_elemento_circuito(partes, el, cx, y_arriba, hueco_top)
        x_prev = cx + hueco_top
    partes.append(f'<line x1="{x_prev:.1f}" y1="{y_arriba:.1f}" x2="{x_der:.1f}" y2="{y_arriba:.1f}" stroke="#2563eb" stroke-width="3"/>')

    partes.append('</svg>')
    return ''.join(partes).encode('utf-8')


def _generar_svg_fluidos_compuerta(nivel_agua: str, profundidad_compuerta: str, dato_compuerta: str) -> bytes:
    """
    Tanque abierto con agua hasta un nivel, una compuerta/orificio en la
    pared lateral con el agua saliendo por ahí. "nivel_agua" etiqueta la
    altura total de la columna de agua; "profundidad_compuerta" es la cota
    vertical desde la superficie hasta la compuerta (el dato que de verdad
    se usa para calcular la velocidad de salida); "dato_compuerta" etiqueta
    el propio orificio (área, ancho o coeficiente).
    """
    tanque_x = 180.0
    tanque_ancho = 200.0
    tanque_y_fondo = 310.0
    tanque_y_superficie = 100.0
    pared_der = tanque_x + tanque_ancho
    y_compuerta = 220.0

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO_SVG}" height="{ALTO_SVG}" '
        f'viewBox="0 0 {ANCHO_SVG} {ALTO_SVG}" font-family="sans-serif">',
        '<defs><marker id="flecha-agua" markerWidth="8" markerHeight="8" refX="6" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#1d4ed8"/></marker></defs>',
        f'<rect width="{ANCHO_SVG}" height="{ALTO_SVG}" fill="#ffffff"/>',
        f'<rect x="{tanque_x:.1f}" y="{tanque_y_superficie:.1f}" width="{tanque_ancho:.1f}" '
        f'height="{tanque_y_fondo - tanque_y_superficie:.1f}" fill="#bfdbfe" opacity="0.6"/>',
        f'<path d="M {tanque_x:.1f} {tanque_y_superficie - 10:.1f} L {tanque_x:.1f} {tanque_y_fondo:.1f} '
        f'L {pared_der:.1f} {tanque_y_fondo:.1f} L {pared_der:.1f} {tanque_y_superficie - 10:.1f}" '
        f'fill="none" stroke="#1e293b" stroke-width="3"/>',
        f'<line x1="{tanque_x - 8:.1f}" y1="{tanque_y_superficie:.1f}" x2="{pared_der + 8:.1f}" '
        f'y2="{tanque_y_superficie:.1f}" stroke="#1d4ed8" stroke-width="2" stroke-dasharray="4 3"/>',
        f'<text x="{tanque_x + tanque_ancho / 2:.1f}" y="{tanque_y_superficie - 14:.1f}" '
        f'font-size="13" fill="#1d4ed8" text-anchor="middle">{_escapar_xml(nivel_agua)}</text>',
    ]

    cota_x = tanque_x - 36
    partes.append(f'<line x1="{cota_x:.1f}" y1="{tanque_y_superficie:.1f}" x2="{cota_x:.1f}" y2="{y_compuerta:.1f}" stroke="#1e293b" stroke-width="1.5"/>')
    partes.append(f'<line x1="{cota_x - 5:.1f}" y1="{tanque_y_superficie:.1f}" x2="{cota_x + 5:.1f}" y2="{tanque_y_superficie:.1f}" stroke="#1e293b" stroke-width="1.5"/>')
    partes.append(f'<line x1="{cota_x - 5:.1f}" y1="{y_compuerta:.1f}" x2="{cota_x + 5:.1f}" y2="{y_compuerta:.1f}" stroke="#1e293b" stroke-width="1.5"/>')
    partes.append(
        f'<text x="{cota_x - 8:.1f}" y="{(tanque_y_superficie + y_compuerta) / 2 + 4:.1f}" '
        f'font-size="13" fill="#1e293b" text-anchor="end">{_escapar_xml(profundidad_compuerta)}</text>'
    )

    alto_compuerta = 20.0
    partes.append(
        f'<rect x="{pared_der - 3:.1f}" y="{y_compuerta - alto_compuerta / 2:.1f}" width="8" '
        f'height="{alto_compuerta:.1f}" fill="#f59e0b" stroke="#92400e" stroke-width="1.5"/>'
    )
    partes.append(
        f'<line x1="{pared_der + 5:.1f}" y1="{y_compuerta:.1f}" x2="{pared_der + 70:.1f}" y2="{y_compuerta:.1f}" '
        f'stroke="#1d4ed8" stroke-width="2.5" marker-end="url(#flecha-agua)"/>'
    )
    partes.append(
        f'<text x="{pared_der + 14:.1f}" y="{y_compuerta - 10:.1f}" font-size="13" '
        f'fill="#1e293b">{_escapar_xml(dato_compuerta)}</text>'
    )

    partes.append('</svg>')
    return ''.join(partes).encode('utf-8')


def generar_variantes_problema_visual(objetivo_texto: str, tema_curso: str, cantidad: int = 5) -> dict:
    """
    Devuelve {"enunciado": str, "variantes": [{"opciones": [...], "respuesta_correcta": int, "imagen_bytes": bytes}, ...]}.
    `imagen_bytes` es un SVG (no PNG) — quien lo guarde debe usar extensión .svg.
    El estilo del diagrama ("ruta", "circuito" o "fluidos_compuerta") lo elige
    la propia IA según el objetivo — ver `_generar_texto_variantes`.
    """
    datos = _generar_texto_variantes(objetivo_texto, tema_curso, cantidad)
    tipo_diagrama = datos['tipo_diagrama']

    variantes = []
    for v in datos['variantes']:
        if tipo_diagrama == 'ruta':
            imagen_bytes = _generar_svg_ruta(v['puntos'], v['segmentos'])
        elif tipo_diagrama == 'circuito':
            imagen_bytes = _generar_svg_circuito(v['elementos'])
        else:
            imagen_bytes = _generar_svg_fluidos_compuerta(
                v['nivel_agua'], v['profundidad_compuerta'], v['dato_compuerta']
            )
        variantes.append({
            'opciones': v['opciones'],
            'respuesta_correcta': v['respuesta_correcta'],
            'imagen_bytes': imagen_bytes,
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
