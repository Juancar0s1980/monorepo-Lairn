# Estructura del Proyecto

Mapa completo del repositorio con descripcion de cada carpeta y archivo importante.

```
backend_lairn/
│
├── .env                          # Variables de entorno (no se sube a git)
├── .env.example                  # Plantilla de variables de entorno
├── .gitignore
├── .dockerignore
├── manage.py                     # Punto de entrada de comandos Django
├── requirements.txt              # Dependencias de Python
├── Dockerfile                    # Imagen Docker del servidor
├── docker-compose.yml            # Orquestacion de contenedores (web + db)
│
├── backend_lairn/                # Configuracion principal de Django
│   ├── settings.py              # Ajustes globales: BD, apps, JWT, DRF
│   ├── urls.py                  # Router raiz de todas las rutas
│   ├── wsgi.py                  # Punto de entrada WSGI (produccion)
│   └── asgi.py                  # Punto de entrada ASGI
│
├── core/                         # Utilidades compartidas entre apps
│   ├── permissions/
│   │   └── permisos_rol.py      # Clases de permisos por rol (EsDocente, EsEstudiante, etc.)
│   ├── services/                # Logica de negocio compartida
│   ├── utils/                   # Funciones auxiliares
│   └── validators/              # Validadores reutilizables
│
├── apps/                         # Modulos principales de la aplicacion
│   │
│   ├── users/                   # Autenticacion y gestion de usuarios
│   │   ├── models/
│   │   │   ├── user.py         # Modelo User personalizado (login por email)
│   │   │   └── role.py         # Modelo Role (Administrador, Docente, Estudiante)
│   │   ├── views/
│   │   │   ├── vista_registrar.py
│   │   │   ├── vista_iniciar_sesion.py
│   │   │   ├── vista_mis_datos.py
│   │   │   └── vista_cerrar_sesion.py
│   │   ├── serializers/
│   │   ├── urls.py              # Rutas: /api/usuarios/
│   │   ├── migrations/
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_roles.py    # Crea los 3 roles base
│   │           └── seed_usuarios.py # Crea usuarios de prueba
│   │
│   ├── examenes/                # Cursos, examenes e inscripciones
│   │   ├── models/
│   │   │   ├── curso.py        # Modelo Curso (con codigo unico de 8 chars)
│   │   │   ├── examen.py       # Modelo Examen (modo fijo o maestria)
│   │   │   └── inscripcion.py  # Relacion estudiante-curso
│   │   ├── views/
│   │   │   ├── vista_crear_curso.py
│   │   │   ├── vista_crear_examen.py
│   │   │   ├── vista_inscribirse.py
│   │   │   └── vista_gestionar_estudiantes.py
│   │   ├── serializers/
│   │   ├── urls.py              # Rutas: /api/examenes/
│   │   └── migrations/
│   │
│   ├── motor_adaptativo/        # Motor de examenes con IA
│   │   ├── models/
│   │   │   ├── sesion_examen.py       # Sesion activa de un examen
│   │   │   └── modelo_conocimiento.py # Mapa de conceptos del estudiante
│   │   ├── views/
│   │   │   ├── vista_iniciar_examen.py
│   │   │   └── vista_responder.py
│   │   ├── services/
│   │   │   └── agente_ia.py    # Integracion con Claude Haiku (generacion de preguntas)
│   │   ├── serializers/
│   │   ├── urls.py              # Rutas: /api/motor-adaptativo/
│   │   └── migrations/
│   │
│   ├── analitica/               # Resultados y estadisticas
│   │   ├── models/
│   │   │   ├── resultado.py           # Resultado final de un examen
│   │   │   └── respuesta_estudiante.py # Registro de cada respuesta individual
│   │   ├── views/
│   │   │   ├── vista_resultados.py
│   │   │   ├── vista_avance_estudiante.py
│   │   │   ├── vista_modelo_conocimiento.py
│   │   │   ├── vista_patrones_curso.py
│   │   │   └── vista_resumen_curso.py
│   │   ├── serializers/
│   │   ├── urls.py              # Rutas: /api/analitica/
│   │   └── migrations/
│   │
│   └── moderacion/              # Pendiente de implementacion
│       ├── models/
│       ├── views/
│       ├── serializers/
│       └── urls.py              # Rutas: /api/moderacion/
│
└── docs/                        # Esta documentacion
    ├── POR_DONDE_EMPEZAR.md
    ├── INICIO_RAPIDO.md
    ├── INSTALACION.md
    ├── VARIABLES_ENTORNO.md
    ├── ESTRUCTURA.md
    ├── ARQUITECTURA.md
    ├── AUTENTICACION.md
    ├── BASE_DE_DATOS.md
    ├── MANEJO_ERRORES.md
    ├── SEGURIDAD.md
    ├── CONTRIBUIR.md
    ├── RESUMEN_PROYECTO.md
    └── COMANDOS.md
```

---

## Convencion de nombres

El proyecto usa nombres en Espanol para mantener consistencia con el dominio:

| Tipo de archivo | Prefijo | Ejemplo |
|-----------------|---------|---------|
| Vistas | `vista_` | `vista_iniciar_sesion.py` |
| Serializadores | `serializador_` | `serializador_usuario.py` |
| Modelos | nombre del modelo | `user.py`, `curso.py` |
| Permisos | `permisos_` | `permisos_rol.py` |

---

## Como fluye una peticion

```
Cliente HTTP
    ↓
backend_lairn/urls.py       (router raiz, distribuye por prefijo /api/...)
    ↓
apps/<nombre>/urls.py       (rutas especificas de cada app)
    ↓
apps/<nombre>/views/        (logica de la vista, valida permisos)
    ↓
apps/<nombre>/serializers/  (validacion y serializacion de datos)
    ↓
apps/<nombre>/models/       (acceso a la base de datos)
    ↓
Respuesta JSON
```

Para el motor adaptativo, la vista tambien llama a `motor_adaptativo/services/agente_ia.py` que se comunica con la API de Claude.
