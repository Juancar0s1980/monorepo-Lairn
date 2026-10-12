# Muestras ICFES (referencia para la IA generadora)

Ítems representativos extraídos de los cuadernillos de preguntas auténticos del ICFES
(Saber Pro, módulos genéricos, publicación 2018) que el equipo cargó en
`docs/cuadernillos_icfes/`. Se usan como **modelo de formato, extensión y nivel de
dificultad** al construir el prompt del agente (`services/agente_saber_pro.py`).

## Fuente y derechos de autor

- Autoría: © Icfes, 2018. Cuadernillos de preguntas Saber Pro (módulos de lectura
  crítica, razonamiento cuantitativo, competencias ciudadanas, comunicación escrita e
  inglés). Solo se autoriza su uso para fines académicos (condiciones de uso del ICFES).
- Estos archivos transcriben **algunos pasajes necesarios** con fines académicos de
  cita (derecho de cita contemplado en las condiciones del ICFES). No se reproduce el
  cuadernillo completo ni se altera el contenido original.
- El prompt inyectado le ordena a la IA NO copiar el contenido de estos ejemplos: solo
  imitar la forma y el nivel, creando variaciones nuevas.

## Reglas de uso (aplicadas en `agente_saber_pro.py`)

1. Cada archivo se inyecta como contexto adicional en el prompt de generación.
2. La IA debe usarlos únicamente como referencia de **formato, extensión y nivel**.
3. Nunca copiar el enunciado, las opciones ni los textos base de los ejemplos.
4. Respetar siempre las reglas de cantidad de opciones y estructura de la parte/área.

## Archivos

| Archivo | Área de Saber Pro |
|---------|-------------------|
| `razonamiento_cuantitativo.md` | Razonamiento Cuantitativo |
| `lectura_critica.md` | Lectura Crítica |
| `competencias_ciudadanas.md` | Competencias Ciudadanas |
| `comunicacion_escrita.md` | Comunicación Escrita (consignas) |
| `ingles.md` | Inglés (por parte, mapeada por tarea) |

## Mapeo tarea → parte en Inglés

El cuadernillo de inglés 2018 usa otra numeración (la tarea de relacionar era la
**parte 2** en 2018); la estructura vigente del ICFES la ubica como **parte 1**. Por eso
el agente mapea **por tarea**, no por número del PDF:

| Tarea (cuadernillo 2018) | Parte vigente | Sección en `ingles.md` |
|--------------------------|---------------|------------------------|
| Relacionar palabras (descripciones) | Parte 1 | `clave_relacionar` |
| Avisos (sin ítem auténtico en 2018) | Parte 2 | `clave_avisos` |
| Completar conversaciones | Parte 3 | `clave_conversaciones` |
| Texto con espacios (3 opciones) | Parte 4 | `clave_texto_espacios` |
| Comprensión literal (paráfrasis) | Parte 5 | `clave_lectura_oneida` + `clave_comprension_literal` |
| Comprensión inferencial | Parte 6 | `clave_lectura_oneida` + `clave_comprension_inferir` |
| Cloze con 4 opciones (sin ítem en 2018) | Parte 7 | `clave_cloze_4` |

Pendientes documentados: para las tareas de la parte 2 (avisos) y la parte 7 (cloze con
4 opciones) no hay ítem auténtico en los cuadernillos cargados; su sección contiene solo
la descripción del formato vigente.