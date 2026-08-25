"""
core/security/decorators.py
Decoradores de seguridad reutilizables para control de acceso RBAC
y protección contra mass assignment.
"""

import logging
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

security_logger = logging.getLogger('security')


def role_required(*allowed_roles):
    """
    Decorador RBAC: restringe acceso solo a usuarios con roles específicos.

    Uso:
        @role_required('admin')
        @role_required('admin', 'instructor')

    Roles válidos: 'admin', 'instructor', 'aprendiz'
    El rol 'admin' incluye automáticamente a is_staff y is_superuser.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('home')

            user_role = getattr(request.user, 'rol', 'aprendiz')

            # Superusers y staff se consideran 'admin'
            if request.user.is_superuser or request.user.is_staff:
                user_role = 'admin'

            if user_role not in allowed_roles:
                security_logger.warning(
                    "Acceso denegado RBAC: usuario=%s (rol=%s) intentó acceder a "
                    "vista=%s (roles requeridos=%s) desde IP=%s",
                    request.user.username,
                    user_role,
                    view_func.__name__,
                    allowed_roles,
                    _get_client_ip(request),
                )

                is_ajax = (
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or 'application/json' in request.headers.get('Accept', '')
                )
                if is_ajax:
                    return JsonResponse(
                        {'error': 'No tienes permisos para esta acción.'},
                        status=403
                    )

                messages.error(
                    request,
                    'Acceso denegado: No tienes permisos para acceder a esta página.'
                )
                return redirect('perfil')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def allowed_fields(*fields):
    """
    Decorador anti mass-assignment: filtra request.POST para que solo
    los campos explícitamente listados sean procesados.

    Uso:
        @allowed_fields('first_name', 'last_name', 'email')
        def admin_editar_usuario(request, user_id):
            ...

    Los campos no incluidos en la whitelist serán eliminados de request.POST.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'POST':
                # Crear copia mutable del QueryDict
                mutable_post = request.POST.copy()
                keys_to_remove = [
                    key for key in mutable_post.keys()
                    if key not in fields and key != 'csrfmiddlewaretoken'
                ]
                for key in keys_to_remove:
                    del mutable_post[key]

                if keys_to_remove:
                    security_logger.info(
                        "Mass assignment bloqueado: usuario=%s eliminó campos=%s "
                        "en vista=%s",
                        getattr(request.user, 'username', 'anon'),
                        keys_to_remove,
                        view_func.__name__,
                    )

                request.POST = mutable_post
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def _get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
