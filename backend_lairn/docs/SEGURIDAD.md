# Seguridad

Consideraciones de seguridad implementadas en LAIRN y configuraciones necesarias antes de pasar a produccion.

---

## Lo que ya esta implementado

### Autenticacion JWT
- Los tokens de acceso expiran en **5 minutos**.
- Los tokens de refresco expiran en **24 horas**.
- El logout invalida el refresh token activo.
- Todos los endpoints protegidos requieren token valido.

### Control de acceso por rol (RBAC)
Cada endpoint valida el rol del usuario mediante clases de permiso definidas en `core/permissions/permisos_rol.py`:

| Clase | Que verifica |
|-------|-------------|
| `EsAdministrador` | El usuario tiene rol `Administrador` |
| `EsDocente` | El usuario tiene rol `Docente` |
| `EsEstudiante` | El usuario tiene rol `Estudiante` |

Un docente no puede responder examenes y un estudiante no puede ver la analitica de otros.

### Validacion de inscripcion
Antes de permitir que un estudiante inicie un examen, el sistema verifica que el estudiante este inscrito en el curso al que pertenece ese examen. Un estudiante no puede iniciar examenes de cursos a los que no pertenece.

### Aislamiento de sesiones
Cada sesion de examen esta ligada al estudiante que la creo. No es posible responder en una sesion que pertenece a otro usuario.

### Variables sensibles fuera del codigo
Las claves (`SECRET_KEY`, `OPENAI_API_KEY`, credenciales de BD) se cargan desde variables de entorno, nunca escritas en el codigo fuente. El archivo `.env` esta en `.gitignore`.

---

## Configuracion obligatoria antes de produccion

### 1. Desactivar el modo debug

```env
DEBUG=False
```

Con `DEBUG=True` Django muestra trazas de error completas en el navegador, exponiendo la estructura interna del proyecto.

### 2. Configurar ALLOWED_HOSTS correctamente

```env
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

Nunca usar `*` en produccion. Esto previene ataques de HTTP Host header.

### 3. Usar una SECRET_KEY fuerte y unica

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

La `SECRET_KEY` se usa para firmar los JWT y las sesiones. Si se filtra, los tokens pueden ser falsificados.

### 4. Forzar HTTPS

Agregar en `settings.py` para produccion:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### 5. Configurar CORS correctamente

Si la API es consumida desde un frontend, limitar los origenes permitidos:

```python
CORS_ALLOWED_ORIGINS = [
    "https://tuapp.com",
]
```

Nunca usar `CORS_ALLOW_ALL_ORIGINS = True` en produccion.

---

## Proteccion de claves de API

### OPENAI_API_KEY
- Esta clave da acceso facturado a la API de OpenAI. Si se filtra, terceros pueden usarla y generar costos.
- Nunca incluirla en el codigo fuente ni en commits.
- En produccion usar un gestor de secretos (AWS Secrets Manager, HashiCorp Vault, variables de entorno del servidor).

### Verificar que .env no esta en git

```bash
git status
# .env NO debe aparecer como archivo tracked
```

Si accidentalmente se subio:

```bash
git rm --cached .env
git commit -m "remove .env from tracking"
```

Y rotar todas las claves comprometidas inmediatamente.

---

## Consideraciones adicionales

### Contrasenas
Django usa `PBKDF2` por defecto para hashear contrasenas. No se almacenan en texto plano.

### Inyeccion SQL
Django ORM protege contra inyeccion SQL por defecto al usar los metodos del queryset. Nunca construir queries con concatenacion de strings.

### Intentos de examen
El campo `max_intentos` en `Examen` limita cuantas veces un estudiante puede intentar el mismo examen (0 = ilimitado). El sistema valida esto antes de crear una nueva sesion.

---

## Checklist de produccion

- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configurado con dominios reales
- [ ] `SECRET_KEY` generada de forma segura y unica
- [ ] HTTPS habilitado y HTTP redirige a HTTPS
- [ ] `OPENAI_API_KEY` en variable de entorno segura (no en .env del repo)
- [ ] `CORS_ALLOWED_ORIGINS` con dominios especificos
- [ ] Logs configurados para monitoreo
- [ ] Backups de base de datos habilitados
