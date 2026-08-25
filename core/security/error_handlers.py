"""
core/security/error_handlers.py
Manejadores de error centralizados para Django.
Stack traces solo en logs internos; cliente recibe mensajes genéricos.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import render

security_logger = logging.getLogger('security')


def handler400(request, exception=None):
    """Bad Request"""
    security_logger.info(
        "400 Bad Request: path=%s ip=%s user=%s",
        request.path,
        _get_ip(request),
        getattr(request.user, 'username', 'anonymous'),
    )
    if _is_ajax(request):
        return JsonResponse(
            {'error': 'Solicitud inválida. Verifica los datos enviados.'},
            status=400
        )
    return render(request, 'errors/400.html', status=400)


def handler403(request, exception=None):
    """Forbidden"""
    security_logger.warning(
        "403 Forbidden: path=%s ip=%s user=%s",
        request.path,
        _get_ip(request),
        getattr(request.user, 'username', 'anonymous'),
    )
    if _is_ajax(request):
        return JsonResponse(
            {'error': 'Acceso denegado. No tienes permisos para esta acción.'},
            status=403
        )
    return render(request, 'errors/403.html', status=403)


def handler404(request, exception=None):
    """Not Found"""
    if _is_ajax(request):
        return JsonResponse(
            {'error': 'Recurso no encontrado.'},
            status=404
        )
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Internal Server Error — NUNCA revelar detalles al cliente"""
    security_logger.error(
        "500 Internal Error: path=%s ip=%s user=%s",
        request.path,
        _get_ip(request),
        getattr(request.user, 'username', 'anonymous'),
        exc_info=True,  # Incluye el stack trace completo en los logs
    )
    if _is_ajax(request):
        return JsonResponse(
            {'error': 'Error interno del servidor. Intenta de nuevo más tarde.'},
            status=500
        )
    return render(request, 'errors/500.html', status=500)


def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )


def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
