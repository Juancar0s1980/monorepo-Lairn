"""
Paquete de URLs de la app `examenes`.

Actúa como punto de entrada único que el proyecto raíz monta bajo
`api/examenes/` y delega la definición concreta de rutas a dos submódulos
divididos por rol del consumidor (Docente / Estudiante).

La división por rol replica la estructura del paquete `views` y permite que
cada equipo o iteración futura agregue endpoints al archivo de su rol sin
tener que tocar un archivo monolítico. Los dos `include` se montan en la
misma raíz (`''`) porque las rutas internas ya son disjuntas y los nombres
de cada `path` son únicos en todo el namespace.
"""

from django.urls import include, path

urlpatterns = [
    # Rutas accedidas por el rol Docente (gestión de cursos, exámenes y estudiantes inscritos).
    path('', include('apps.examenes.urls.docente')),

    # Rutas accedidas por el rol Estudiante (inscripción y consulta de cursos/exámenes).
    path('', include('apps.examenes.urls.estudiante')),

    # Rutas accedidas por el rol Administrador (supervisión global de exámenes).
    path('', include('apps.examenes.urls.administrador')),
]
