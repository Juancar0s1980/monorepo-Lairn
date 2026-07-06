from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'Administrador'
        )


class EsDocente(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'Docente'
        )


class EsEstudiante(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'Estudiante'
        )
