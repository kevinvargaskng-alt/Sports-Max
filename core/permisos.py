"""
core/permisos.py - CP-16: Sistema de control de acceso por roles
Sports-Max SENA
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


# ─────────────────────────────────────────────────────────────
# ROLES DEL SISTEMA
# ─────────────────────────────────────────────────────────────
ROLES = {
    'aprendiz':      'Aprendiz',
    'entrenador':    'Entrenador',
    'nutricionista': 'Nutricionista',
    'instructor':    'Instructor',
    'administrador': 'Administrador',
}

# Badge colors for UI rendering (Bootstrap 5)
ROL_COLORES = {
    'aprendiz':      'success',
    'entrenador':    'primary',
    'nutricionista': 'purple',    # CSS personalizado en style.css
    'instructor':    'warning',
    'administrador': 'danger',
}

# FontAwesome icons per role
ROL_ICONOS = {
    'aprendiz':      'fa-user',
    'entrenador':    'fa-dumbbell',
    'nutricionista': 'fa-apple-whole',
    'instructor':    'fa-chalkboard-teacher',
    'administrador': 'fa-shield-halved',
}


# ─────────────────────────────────────────────────────────────
# HELPERS DE ROL
# ─────────────────────────────────────────────────────────────
def es_admin(usuario):
    """Retorna True si el usuario es administrador o superusuario."""
    return bool(usuario and usuario.is_authenticated and
                (usuario.rol == 'administrador' or usuario.is_superuser))


def es_profesional_salud(usuario):
    """Nutricionistas, entrenadores y administradores."""
    return bool(usuario and usuario.is_authenticated and
                usuario.rol in ('nutricionista', 'entrenador', 'administrador'))


def es_nutricionista(usuario):
    return bool(usuario and usuario.is_authenticated and
                usuario.rol in ('nutricionista', 'administrador') or
                (hasattr(usuario, 'is_superuser') and usuario.is_superuser))


def es_entrenador(usuario):
    return bool(usuario and usuario.is_authenticated and
                usuario.rol in ('entrenador', 'administrador') or
                (hasattr(usuario, 'is_superuser') and usuario.is_superuser))


def es_instructor(usuario):
    return bool(usuario and usuario.is_authenticated and
                usuario.rol in ('instructor', 'administrador') or
                (hasattr(usuario, 'is_superuser') and usuario.is_superuser))


# ─────────────────────────────────────────────────────────────
# DECORADOR DE ROL PARA VISTAS BASADAS EN FUNCIONES
# ─────────────────────────────────────────────────────────────
def requiere_rol(*roles):
    """
    Decorador que restringe el acceso a usuarios con alguno de los roles indicados.
    Requiere que el usuario esté autenticado (implica @login_required).

    Uso:
        @requiere_rol('nutricionista', 'administrador')
        def mi_vista(request):
            ...
    """
    def decorador(vista_func):
        @wraps(vista_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            usuario = request.user
            # Superusuarios pasan siempre
            if usuario.is_superuser:
                return vista_func(request, *args, **kwargs)
            # Verificar si el rol del usuario está entre los permitidos
            if hasattr(usuario, 'rol') and usuario.rol in roles:
                return vista_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorador


# ─────────────────────────────────────────────────────────────
# MIXIN PARA VISTAS BASADAS EN CLASES (CBV)
# ─────────────────────────────────────────────────────────────
class RolRequeridoMixin:
    """
    Mixin para CBVs que restringe el acceso según roles.

    Uso:
        class MiVista(RolRequeridoMixin, ListView):
            roles_permitidos = ['nutricionista', 'administrador']
    """
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if hasattr(request.user, 'rol') and request.user.rol in self.roles_permitidos:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
