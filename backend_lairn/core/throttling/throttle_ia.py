"""
Throttle para endpoints que llaman a un proveedor de IA (Groq/OpenAI/Gemini).

Estos endpoints son los únicos con un costo real por request (facturación del
proveedor de IA) y los únicos donde un loop de un estudiante/docente puede
generar gasto — a diferencia del resto de la API, que solo lee/escribe en la
propia base de datos. `ScopedRateThrottle` de DRF ya soporta justo este caso:
un límite MÁS ESTRICTO que el general, aplicado únicamente a las vistas que
declaran `throttle_scope = 'ia'`.

Se usa AL LADO de `UserRateThrottle` (no en su lugar) en cada vista: la
general sigue protegiendo contra abuso genérico de la API, esta protege
específicamente el costo de IA. Ver `DEFAULT_THROTTLE_RATES` en settings.py
para los límites configurados.
"""

from rest_framework.throttling import ScopedRateThrottle


class ThrottleIA(ScopedRateThrottle):
    scope = 'ia'
