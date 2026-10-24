"""
Helpers compartidos para los tests de todas las apps: crear usuarios con rol,
cursos, inscripciones, y mockear el cliente de IA sin tocar la red.

No es una app de Django (no tiene modelos ni está en INSTALLED_APPS) — es un
paquete de utilidades puras que cualquier `apps/<app>/tests/` importa.
"""

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from apps.users.models import Role, User
from apps.examenes.models import Curso, Inscripcion


def _crear_usuario(email: str, rol_nombre: str, **kwargs) -> User:
    rol, _ = Role.objects.get_or_create(name=rol_nombre)
    datos = {
        'first_name': kwargs.pop('first_name', 'Nombre'),
        'first_last_name': kwargs.pop('first_last_name', 'Apellido'),
        **kwargs,
    }
    usuario = User.objects.create_user(email=email, password='clave-test-123', **datos)
    usuario.role = rol
    usuario.save()
    return usuario


def crear_docente(email: str = 'docente@test.com', **kwargs) -> User:
    return _crear_usuario(email, 'Docente', **kwargs)


def crear_estudiante(email: str = 'estudiante@test.com', **kwargs) -> User:
    return _crear_usuario(email, 'Estudiante', **kwargs)


def crear_administrador(email: str = 'admin@test.com', **kwargs) -> User:
    return _crear_usuario(email, 'Administrador', **kwargs)


def crear_curso(docente: User, nombre: str = 'Curso de prueba', **kwargs) -> Curso:
    return Curso.objects.create(docente=docente, nombre=nombre, **kwargs)


def inscribir(estudiante: User, curso: Curso) -> Inscripcion:
    return Inscripcion.objects.create(estudiante=estudiante, curso=curso)


@contextmanager
def mock_cliente_ia(modulo_agente: str, respuesta_json: dict, modelo: str = 'modelo-test', kwarg_max_tokens: str = 'max_tokens'):
    """
    Parcha `obtener_cliente_ia()` en el MÓDULO DEL AGENTE indicado (ej.
    "apps.motor_adaptativo.services.agente_ia") para que devuelva un cliente
    falso cuyo `chat.completions.create(...)` siempre responde
    `respuesta_json` (ya serializado a JSON) como el content del mensaje.

    Se parcha en el módulo que USA la función (no en `backend_lairn.ia_client`
    donde se define) porque cada agente hace
    `from backend_lairn.ia_client import obtener_cliente_ia`, que copia el
    nombre a su propio namespace — parchar el original no afecta esa copia.

    Nunca toca la red: ningún test que use esto debería demorar más de una
    fracción de segundo ni depender de que un proveedor de IA esté disponible.
    """
    cliente_falso = MagicMock()
    mensaje = MagicMock()
    mensaje.content = json.dumps(respuesta_json)
    respuesta = MagicMock()
    respuesta.choices = [MagicMock(message=mensaje)]
    cliente_falso.chat.completions.create.return_value = respuesta

    with patch(f'{modulo_agente}.obtener_cliente_ia', return_value=(cliente_falso, modelo, kwarg_max_tokens)):
        yield cliente_falso
