# Como Contribuir

Guia para desarrolladores que quieran agregar funcionalidades, corregir errores o mejorar el proyecto.

---

## Antes de empezar

1. Asegurate de tener el proyecto corriendo localmente. Ver [INSTALACION.md](INSTALACION.md) o [INICIO_RAPIDO.md](INICIO_RAPIDO.md).
2. Lee [ESTRUCTURA.md](ESTRUCTURA.md) para entender como esta organizado el codigo.
3. Lee [ARQUITECTURA.md](ARQUITECTURA.md) para entender el flujo del sistema.

---

## Flujo de trabajo

```
1. Crea una rama desde main
2. Implementa el cambio
3. Crea las migraciones si modificaste modelos
4. Verifica que no rompe nada existente
5. Crea el Pull Request
```

### Crear una rama

```bash
git checkout main
git pull origin main
git checkout -b feature/nombre-descriptivo
# o para bugs:
git checkout -b fix/descripcion-del-bug
```

---

## Convenciones de nombres

El proyecto usa **Espanol** para todos los archivos, variables y nombres de funciones relacionados con el dominio.

| Tipo | Convencion | Ejemplo |
|------|-----------|---------|
| Vistas | `vista_<accion>.py` | `vista_crear_curso.py` |
| Serializadores | `serializador_<modelo>.py` | `serializador_examen.py` |
| Modelos | `<modelo>.py` | `curso.py`, `sesion_examen.py` |
| Permisos | `permisos_<tipo>.py` | `permisos_rol.py` |
| URLs | `urls.py` (estandar Django) | — |
| Comandos de gestion | nombre en Espanol | `seed_roles.py` |

---

## Como agregar una nueva app

1. Crear la carpeta dentro de `apps/`:

```bash
mkdir apps/nueva_app
```

2. Crear la estructura interna:

```
apps/nueva_app/
├── __init__.py
├── apps.py
├── urls.py
├── models/
│   └── __init__.py
├── views/
│   └── __init__.py
├── serializers/
│   └── __init__.py
└── migrations/
    └── __init__.py
```

3. Registrar en `backend_lairn/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'apps.nueva_app',
]
```

4. Registrar las URLs en `backend_lairn/urls.py`:

```python
path('api/nueva-app/', include('apps.nueva_app.urls')),
```

---

## Como agregar un nuevo endpoint

1. Crear la vista en `apps/<nombre>/views/vista_<accion>.py`:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions.permisos_rol import EsDocente

class MiNuevaVista(APIView):
    permission_classes = [IsAuthenticated, EsDocente]

    def get(self, request):
        return Response({"mensaje": "hola"})
```

2. Registrar en `apps/<nombre>/urls.py`:

```python
from django.urls import path
from .views.vista_nueva import MiNuevaVista

urlpatterns = [
    path('mi-endpoint/', MiNuevaVista.as_view(), name='mi-endpoint'),
]
```

---

## Como agregar un nuevo modelo

1. Crear el archivo en `apps/<nombre>/models/<modelo>.py`
2. Importarlo en `apps/<nombre>/models/__init__.py`
3. Crear la migracion:

```bash
python manage.py makemigrations <nombre_app>
python manage.py migrate
```

---

## Permisos disponibles

Ubicados en `core/permissions/permisos_rol.py`:

| Clase | Cuando usarla |
|-------|--------------|
| `IsAuthenticated` | Cualquier usuario autenticado (sin importar rol) |
| `EsAdministrador` | Solo administradores |
| `EsDocente` | Solo docentes |
| `EsEstudiante` | Solo estudiantes |

Pueden combinarse:

```python
permission_classes = [IsAuthenticated, EsDocente]
```

---

## Comandos utiles durante el desarrollo

```bash
# Ver todas las rutas registradas
python manage.py show_urls

# Abrir shell interactivo de Django
python manage.py shell

# Ver migraciones pendientes
python manage.py showmigrations

# Revertir una migracion
python manage.py migrate <app_name> <numero_migracion_anterior>

# Limpiar la base de datos y empezar de cero
python manage.py flush

# Volver a crear roles y usuarios de prueba
python manage.py seed_roles
python manage.py seed_usuarios
```

---

## Estructura de un Pull Request

El titulo debe ser descriptivo y en Espanol:
- `feat: agregar endpoint de exportacion de resultados`
- `fix: corregir calculo de nota en modo maestria`
- `refactor: separar logica de inscripcion en servicio`

La descripcion debe incluir:
- Que cambia y por que
- Como probarlo
- Si agrega migraciones
