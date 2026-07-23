"""
Punto único para obtener el cliente de IA generativa usado por
`agente_ia` (motor_adaptativo) y `agente_codigo` (laboratorios).

El proveedor se elige con la variable de entorno AI_PROVIDER ("openai",
"grok" o "groq"). Las tres APIs son compatibles con el SDK de OpenAI:
mismo paquete `openai`, solo cambian `base_url`, la API key y el nombre
del modelo. Por eso los tres casos reutilizan `openai.OpenAI(...)`.

Nota: "grok" (xAI, console.x.ai) y "groq" (Groq Cloud, console.groq.com)
son proveedores distintos que solo se parecen en el nombre.

`kwarg_max_tokens` indica qué nombre de parámetro usar para el tope de
tokens en `chat.completions.create`: los modelos razonadores de OpenAI
(gpt-5.x) exigen `max_completion_tokens`; Grok y Groq usan el `max_tokens`
estándar de la Chat Completions API.
"""

import openai
from django.conf import settings

_MODELOS = {
    "openai": "gpt-5.5",
    "grok": "grok-4.5",
    "groq": "llama-3.3-70b-versatile",
}


def obtener_cliente_ia() -> tuple[openai.OpenAI, str, str]:
    proveedor = settings.AI_PROVIDER

    if proveedor == "grok":
        client = openai.OpenAI(api_key=settings.XAI_API_KEY, base_url="https://api.x.ai/v1")
        return client, _MODELOS["grok"], "max_tokens"

    if proveedor == "groq":
        client = openai.OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        return client, _MODELOS["groq"], "max_tokens"

    if proveedor == "openai":
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        return client, _MODELOS["openai"], "max_completion_tokens"

    raise ValueError(f'AI_PROVIDER desconocido: "{proveedor}" (usa "openai", "grok" o "groq")')
