"""
Generación de preguntas y laboratorios de código con IA.

Dos flujos:
1. `generar_borrador_pregunta`: una pregunta por objetivo del curso (igual
   que la IA ancla preguntas de examen a los objetivos en
   `motor_adaptativo.services.agente_ia`) — la IA elige el lenguaje más
   apropiado para cada objetivo.
2. `generar_laboratorio_libre`: el docente escribe un enunciado libre
   describiendo qué laboratorio quiere y ELIGE el lenguaje explícitamente;
   la IA genera el laboratorio completo (título + N preguntas) en ese
   lenguaje.

En ambos casos la IA también entrega una "solución de referencia" (código
que resuelve el ejercicio correctamente). Esa solución NUNCA se guarda ni
se muestra al estudiante — se ejecuta en el sandbox (mismo `microservicio
ejecutor` que corre el código del estudiante) para obtener la salida REAL
de cada caso de test, en vez de confiar en que la IA calculó bien a mano la
salida esperada. Si la IA se equivoca en la lógica, la ejecución lo revela
(error o timeout) y ese caso se descarta en vez de colar un test roto — ver
`apps.laboratorios.services.verificador_casos`.
"""

import json
import openai
from django.conf import settings

MAX_INTENTOS = 2

LENGUAJES_SOPORTADOS = ('python', 'javascript', 'java', 'cpp', 'c', 'sql')

_REGLAS_POR_LENGUAJE = """- Python: "codigo_inicial" es una plantilla corta (2-4 líneas). "solucion_referencia" lee
  la entrada con input() e imprime el resultado con print().
- JavaScript (Node.js): "solucion_referencia" lee stdin completo con
  require("fs").readFileSync(0, "utf8") e imprime con console.log().
- Java: la clase pública DEBE llamarse exactamente "Main" (archivo Main.java). Lee con
  java.util.Scanner e imprime con System.out.println().
- C++: incluye <iostream>, lee con std::cin e imprime con std::cout.
- C: incluye <stdio.h>, lee con scanf e imprime con printf.
- SQL: "setup_sql" son las sentencias CREATE TABLE/INSERT que crean y pueblan las tablas.
  "solucion_referencia" es UNA consulta SELECT completa y correcta contra ese esquema.
  "codigo_inicial" va vacío. Para los demás lenguajes, "setup_sql" va vacío."""


def _validar_borrador(datos: dict, forzar_enunciado: bool = True) -> None:
    if not isinstance(datos, dict):
        raise ValueError('la respuesta no es un objeto JSON')

    requeridas = ['enunciado', 'lenguaje', 'codigo_inicial', 'setup_sql', 'solucion_referencia', 'casos']
    if not forzar_enunciado:
        requeridas.remove('enunciado')
    faltantes = [c for c in requeridas if c not in datos]
    if faltantes:
        raise ValueError(f'faltan claves: {", ".join(faltantes)}')

    if datos['lenguaje'] not in LENGUAJES_SOPORTADOS:
        raise ValueError(f'lenguaje debe ser uno de {LENGUAJES_SOPORTADOS}')
    if forzar_enunciado and not str(datos['enunciado']).strip():
        raise ValueError('enunciado vacío')
    if not str(datos['solucion_referencia']).strip():
        raise ValueError('solucion_referencia vacía')

    casos = datos['casos']
    if not isinstance(casos, list) or not (1 <= len(casos) <= 6):
        raise ValueError('casos debe ser una lista de 1 a 6 elementos')
    for caso in casos:
        if not isinstance(caso, dict) or 'entrada' not in caso or 'es_publico' not in caso:
            raise ValueError('cada caso necesita "entrada" y "es_publico"')


def generar_borrador_pregunta(objetivo_texto: str, tema_curso: str) -> dict:
    """
    Pide a la IA un borrador de pregunta de código para un objetivo puntual.
    La IA elige el lenguaje más apropiado para ese objetivo. Devuelve el
    borrador SIN VERIFICAR (ver `verificador_casos.verificar_casos`).
    """
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    mensaje = f"""Eres un diseñador de ejercicios de programación para un curso universitario.
Genera UN ejercicio de código que evalúe exactamente el siguiente objetivo de aprendizaje.
Tu única salida debe ser un objeto JSON válido, sin texto adicional.

Curso: "{tema_curso}"
Objetivo a evaluar: "{objetivo_texto}"

Reglas:
1. Elige "lenguaje" entre {LENGUAJES_SOPORTADOS}: usa "sql" solo si el objetivo trata
   explícitamente sobre bases de datos o consultas; para el resto, elige el lenguaje de
   programación general más apropiado al objetivo (por defecto "python" si no hay pista clara).
2. El ejercicio debe ser autocontenido, de dificultad apropiada para un estudiante universitario
   (ni trivial tipo "imprime hola mundo", ni de nivel competitivo).
3. Reglas de entrada/salida por lenguaje:
{_REGLAS_POR_LENGUAJE}
4. Genera entre 2 y 4 "casos": cada uno con "entrada" (stdin para lenguajes de código, o DDL/DML
   ADICIONAL opcional para SQL — puede ser cadena vacía) y "es_publico" (bool). Al menos un caso
   debe ser público (es_publico=true) para mostrarlo de ejemplo, y al menos uno oculto.
5. En español, salvo identificadores de código.

Formato de salida (únicamente estas claves):
{{
  "enunciado": "texto del ejercicio para el estudiante",
  "lenguaje": "uno de los lenguajes soportados",
  "codigo_inicial": "plantilla o cadena vacía",
  "setup_sql": "DDL/DML o cadena vacía",
  "solucion_referencia": "código o consulta que resuelve el ejercicio",
  "casos": [{{"entrada": "...", "es_publico": true}}]
}}"""

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model='gpt-5.5',
            # Margen amplio: los tokens de razonamiento de gpt-5.5 consumen este
            # presupuesto y un tope corto devuelve contenido vacío.
            max_completion_tokens=3000,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            _validar_borrador(datos)
            return datos
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo una pregunta de código válida tras {MAX_INTENTOS} intentos: {ultimo_error}')


def generar_laboratorio_libre(enunciado_docente: str, lenguaje: str, cantidad_preguntas: int = 3) -> dict:
    """
    Genera un laboratorio COMPLETO (título + instrucciones + N preguntas) a
    partir de una descripción libre del docente, en el lenguaje que el
    docente eligió explícitamente (la IA no lo decide acá, a diferencia de
    `generar_borrador_pregunta`). Devuelve el borrador SIN VERIFICAR.
    """
    if lenguaje not in LENGUAJES_SOPORTADOS:
        raise ValueError(f'Lenguaje no soportado: {lenguaje}')

    cantidad_preguntas = max(1, min(cantidad_preguntas, 8))
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    mensaje = f"""Eres un diseñador de laboratorios de programación para un curso universitario.
El docente describió qué laboratorio quiere. Genera el laboratorio COMPLETO: un título, unas
instrucciones breves para el estudiante, y exactamente {cantidad_preguntas} preguntas de código
en lenguaje "{lenguaje}", todas relacionadas con la descripción del docente pero cada una
evaluando algo distinto (sin repetirse entre sí). Tu única salida debe ser un objeto JSON válido,
sin texto adicional.

Descripción del docente: "{enunciado_docente}"
Lenguaje obligatorio para TODAS las preguntas: "{lenguaje}"

Reglas por pregunta (misma estructura que un ejercicio individual):
1. Autocontenida, de dificultad apropiada para un estudiante universitario.
2. Reglas de entrada/salida del lenguaje "{lenguaje}":
{_REGLAS_POR_LENGUAJE}
3. Genera entre 2 y 4 "casos" por pregunta: cada uno con "entrada" (stdin, o DDL/DML adicional
   si "{lenguaje}"="sql") y "es_publico" (bool). Al menos uno público y al menos uno oculto.
4. En español, salvo identificadores de código.

Formato de salida (únicamente estas claves):
{{
  "titulo": "título del laboratorio",
  "instrucciones": "instrucciones breves para el estudiante",
  "preguntas": [
    {{
      "enunciado": "texto del ejercicio",
      "lenguaje": "{lenguaje}",
      "codigo_inicial": "plantilla o cadena vacía",
      "setup_sql": "DDL/DML o cadena vacía",
      "solucion_referencia": "código o consulta que resuelve el ejercicio",
      "casos": [{{"entrada": "...", "es_publico": true}}]
    }}
  ]
}}"""

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model='gpt-5.5',
            # Varias preguntas completas en una sola respuesta: presupuesto generoso.
            max_completion_tokens=3000 + 1500 * cantidad_preguntas,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            if not isinstance(datos, dict):
                raise ValueError('la respuesta no es un objeto JSON')
            if not str(datos.get('titulo', '')).strip():
                raise ValueError('falta "titulo"')
            preguntas = datos.get('preguntas')
            if not isinstance(preguntas, list) or not preguntas:
                raise ValueError('falta "preguntas" o está vacía')
            for pregunta in preguntas:
                _validar_borrador(pregunta)
                if pregunta['lenguaje'] != lenguaje:
                    raise ValueError('una pregunta no respetó el lenguaje elegido por el docente')
            return {
                'titulo': str(datos['titulo']).strip()[:200],
                'instrucciones': str(datos.get('instrucciones', '')).strip(),
                'preguntas': preguntas,
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo un laboratorio válido tras {MAX_INTENTOS} intentos: {ultimo_error}')
