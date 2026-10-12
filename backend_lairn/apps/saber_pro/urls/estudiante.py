"""
Rutas de la app `saber_pro` accedidas por el rol Estudiante.

La HU-17 es exclusiva del docente (creación y gestión de cursos Saber Pro); los
endpoints del estudiante llegan con la HU-18 (unirse a un curso con el código de
acceso y consultar los cursos a los que pertenece). Este archivo queda creado,
con `urlpatterns` vacío, para no tener que cambiar la estructura del paquete
`urls` cuando esa épica se implemente.
"""

from django.urls import path

urlpatterns = []