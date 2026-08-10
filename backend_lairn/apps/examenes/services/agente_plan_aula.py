"""
Servicio de extracción de objetivos de aprendizaje a partir del PDF del
"plan de aula" institucional que el docente sube al crear un curso.

`extraer_texto_pdf` lee el archivo directamente en memoria (nunca se guarda
a disco ni se asocia a un `FileField`: el PDF se descarta al terminar el
request). `extraer_objetivos_plan_aula` le pasa el texto COMPLETO del
documento a la IA y le pide que lo desglose en dos niveles:
- Los objetivos generales (sección "RESULTADOS DE APRENDIZAJE" o equivalente).
- Objetivos a partir del temario/contenido temático, agrupando con criterio
  profesional los sub-temas afines en un solo objetivo conciso y separando
  solo cuando un sub-tema amerita evaluarse aparte por su peso o
  independencia. No es un volcado 1:1 de la lista del PDF.

Es agnóstico de carrera: el prompt le pide explícitamente a la IA que use el
vocabulario propio de la disciplina del curso (programación, derecho,
mecánica de fluidos, idiomas, etc.), sin asumir que es un curso técnico.

Cada objetivo devuelto se guarda directamente como `ObjetivoCurso` (a
diferencia de `sugerir_objetivos`, que solo propone borradores para que el
docente los cure: aquí el docente ya aprobó el contenido al elegir y subir
ese PDF). Mismo formato de oración corta en infinitivo que usa
`sugerir_objetivos` (apps.motor_adaptativo.services.agente_ia), compatible
con `ObjetivoCurso.descripcion` (máx 200 caracteres).
"""

import json

from pypdf import PdfReader

from backend_lairn.ia_client import obtener_cliente_ia


def extraer_texto_pdf(archivo) -> str:
    lector = PdfReader(archivo)
    paginas = [pagina.extract_text() or '' for pagina in lector.pages]
    return '\n'.join(paginas).strip()


def extraer_objetivos_plan_aula(texto_plan: str, nombre_curso: str) -> list:
    """
    Extrae los objetivos de aprendizaje del texto de un plan de aula.

    Devuelve una lista de strings ya lista para guardar como `ObjetivoCurso`
    (a diferencia de `sugerir_objetivos`, que solo propone borradores para
    que el docente los cure, esta extracción se guarda directamente: el
    docente ya aprobó el contenido al elegir y subir ese PDF).
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    # Recorte defensivo: documentos institucionales rara vez superan esto,
    # y evita mandar de más si el PDF trae anexos largos (bibliografía, etc.).
    texto_recortado = texto_plan[:12000]

    mensaje = f"""Actúa como un experto en diseño curricular universitario. Tu tarea es leer el
plan de aula de un curso y redactar su lista de objetivos de aprendizaje de forma
profesional: precisa, concisa y sin redundancia — la que escribiría un docente
experimentado, no una transcripción mecánica del documento.

Curso: "{nombre_curso}"

Texto COMPLETO extraído del PDF del plan de aula:
---
{texto_recortado}
---

Lee todo el documento y redacta los objetivos combinando estas dos fuentes:

1. OBJETIVOS GENERALES: busca la sección de resultados de aprendizaje del curso
   (suele llamarse "RESULTADOS DE APRENDIZAJE", pero puede tener otro nombre
   similar como "OBJETIVOS" o "COMPETENCIAS ESPECÍFICAS"). Redacta cada uno de
   forma concisa y fiel al original.

2. OBJETIVOS DEL TEMARIO: busca la sección de contenido del curso (suele
   llamarse "CONTENIDO TEMÁTICO", puede tener otro nombre similar como
   "TEMARIO" o "UNIDADES"), normalmente organizada en unidades con sub-temas.
   Para cada unidad, decide con criterio profesional cómo convertirla en
   objetivos:
   - Si varios sub-temas de la misma unidad son afines o se evalúan juntos en
     la práctica, agrúpalos en UN SOLO objetivo conciso que los CUBRA TODOS
     explícitamente — no elijas uno solo y descartes el resto.
   - Sepáralos en objetivos distintos solo cuando un sub-tema tiene peso o
     independencia suficiente para evaluarse aparte.
   - Ningún sub-tema del PDF debe quedar fuera de todos los objetivos
     generados: si agrupas, la redacción debe reflejar cada sub-tema agrupado
     (aunque sea brevemente), no limitarse al primero o al más general.
   - Prefija cada objetivo del temario con el nombre de su unidad y dos
     puntos (ej. "Nombre de la unidad: ...").
   El resultado NO debe ser un volcado 1:1 de cada línea del PDF: es una
   síntesis profesional pensada para anclar preguntas de examen, sin perder
   cobertura de ningún sub-tema.

IMPORTANTE: este curso puede ser de CUALQUIER carrera o materia — programación,
derecho, mecánica de fluidos, idiomas, enfermería, contaduría, historia,
psicología, etc. NO asumas que es un curso de programación ni uses vocabulario
técnico de software si el documento no lo pide. Redacta cada objetivo con el
vocabulario propio de la disciplina del curso. Dos ejemplos del mismo patrón
de agrupamiento en disciplinas distintas:
- Programación — unidad "Condicionales" con sub-temas "Estructuras de
  control", "Sentencias condicionales", "Sentencias condicionales anidadas"
  → "Condicionales: aplicar estructuras de control mediante condicionales
  simples y anidados".
- Derecho — unidad "Contratos" con sub-temas "Elementos esenciales", "Vicios
  del consentimiento", "Causales de nulidad" → "Contratos: analizar los
  elementos esenciales, vicios del consentimiento y causales de nulidad de
  un contrato".

Reglas de redacción (ambas fuentes):
- Una sola oración concisa (nunca más de 25 palabras), que empiece con un
  verbo en infinitivo (ej.: "Aplicar", "Diseñar", "Construir", "Diferenciar").
  Si agrupaste varios sub-temas, prioriza cubrirlos todos por encima de
  acortar aún más la oración.
- Concreto y evaluable con preguntas de examen, no vago ni genérico.
- No inventes contenido que no esté en el texto: sintetiza fielmente lo que
  ya dice el documento.
- Si el documento no tiene una de las dos secciones, genera solo con la que
  sí exista; nunca inventes la sección faltante.

Tu única salida debe ser un objeto JSON válido, sin texto adicional:
{{"objetivos": ["objetivo general 1", "...", "Unidad: objetivo del temario 1", "..."]}}"""

    ultimo_error = None
    for _ in range(2):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 3000},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            objetivos = datos.get('objetivos')
            if not isinstance(objetivos, list) or not objetivos:
                raise ValueError('la clave "objetivos" falta o no es una lista con elementos')
            objetivos = [str(o).strip() for o in objetivos if str(o).strip()]
            if not objetivos:
                raise ValueError('todos los objetivos vinieron vacíos')
            # Recorte defensivo: respeta el límite del modelo ObjetivoCurso (200 chars).
            return [o[:200] for o in objetivos]
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no pudo extraer objetivos válidos del plan de aula tras 2 intentos: {ultimo_error}')
