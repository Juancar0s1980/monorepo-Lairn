from rest_framework.permissions import SAFE_METHODS, BasePermission


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


class EsCoordinador(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'Coordinador'
        )


class EsGestorAcademico(BasePermission):
    """Administrador o Coordinador: estructura curricular (HU-01.3 a HU-02.3)."""

    def has_permission(self, request, view):
        return EsAdministrador().has_permission(request, view) or EsCoordinador().has_permission(request, view)


class EsAdministradorOLecturaCoordinador(BasePermission):
    """El Coordinador consulta (HU-01.3); solo el Administrador crea o edita (HU-01.1/01.2)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return EsGestorAcademico().has_permission(request, view)
        return EsAdministrador().has_permission(request, view)


class EsVicerrector(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'Vicerrector'
        )


class EsLectorAnalitica(BasePermission):
    """Analítica institucional (HU-11 + ADR-011/015): Vicerrector, Administrador o Coordinador, solo lectura.

    El Coordinador se incorporó por decisión del usuario (ADR-015): los directivos que leen el reporte son
    Vicerrectoría, Coordinación y Administración.
    """

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return (EsVicerrector().has_permission(request, view) or EsGestorAcademico().has_permission(request, view))


class EsLectorInstitucional(BasePermission):
    """Reporte ejecutivo (HU-11): Vicerrector (solo lectura) o Administrador.

    Solo se usa en vistas de consulta: el Vicerrector no tiene escritura en ningún módulo.
    """

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return EsAdministrador().has_permission(request, view) or EsVicerrector().has_permission(request, view)
