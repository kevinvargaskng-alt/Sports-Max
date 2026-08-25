"""
core/security/middleware.py
Middlewares de seguridad: Rate Limiting, Security Headers y Audit Logging.
"""

import time
import json
import logging
import hashlib
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

security_logger = logging.getLogger('security')
audit_logger = logging.getLogger('audit')


# ═══════════════════════════════════════════════════════════
#  RATE LIMITING MIDDLEWARE
# ═══════════════════════════════════════════════════════════

class RateLimitMiddleware:
    """
    Rate limiting por IP con límites configurables por tipo de ruta.

    Configuración en settings.py:
        RATE_LIMIT_CONFIG = {
            'login':   {'rate': 5,   'period': 60},   # 5 req/min
            'api':     {'rate': 30,  'period': 60},    # 30 req/min
            'default': {'rate': 100, 'period': 60},    # 100 req/min
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'RATE_LIMIT_CONFIG', {
            'login':   {'rate': 5,   'period': 60},
            'api':     {'rate': 30,  'period': 60},
            'default': {'rate': 100, 'period': 60},
        })

    def __call__(self, request):
        # No aplicar rate limiting a archivos estáticos
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        ip = self._get_client_ip(request)
        route_type = self._classify_route(request.path)
        config = self.config.get(route_type, self.config['default'])

        cache_key = f"ratelimit:{route_type}:{ip}"
        request_count = cache.get(cache_key, 0)

        if request_count >= config['rate']:
            security_logger.warning(
                "Rate limit excedido: IP=%s ruta=%s tipo=%s count=%d/%d",
                ip, request.path, route_type, request_count, config['rate']
            )
            return JsonResponse(
                {
                    'error': 'Demasiadas solicitudes. Intenta de nuevo más tarde.',
                    'retry_after': config['period'],
                },
                status=429,
                headers={'Retry-After': str(config['period'])}
            )

        # Incrementar contador
        try:
            cache.set(cache_key, request_count + 1, config['period'])
        except Exception:
            pass  # Si el cache falla, no bloquear la request

        response = self.get_response(request)
        return response

    def _classify_route(self, path):
        """Clasifica la ruta para aplicar el rate limit adecuado."""
        path_lower = path.lower()
        if '/login' in path_lower or '/registro' in path_lower or '/desbloquear' in path_lower:
            return 'login'
        if '/api/' in path_lower:
            return 'api'
        return 'default'

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ═══════════════════════════════════════════════════════════
#  SECURITY HEADERS MIDDLEWARE
# ═══════════════════════════════════════════════════════════

class SecurityHeadersMiddleware:
    """
    Inyecta cabeceras de seguridad HTTP en todas las respuestas:
    - Content-Security-Policy (CSP)
    - Referrer-Policy
    - Permissions-Policy
    - X-Content-Type-Options (refuerzo)
    - Cache-Control para contenido autenticado
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com",
            "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net cdnjs.cloudflare.com",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "media-src 'self' blob:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy
        response['Permissions-Policy'] = (
            'camera=(), microphone=(self), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )

        # Prevenir caching de contenido autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not request.path.startswith(('/static/', '/media/')):
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
                response['Pragma'] = 'no-cache'

        return response


# ═══════════════════════════════════════════════════════════
#  AUDIT MIDDLEWARE
# ═══════════════════════════════════════════════════════════

# Campos sensibles que se sanitizan antes de loguear
SENSITIVE_FIELDS = frozenset([
    'password', 'contrasena', 'contraseña', 'token', 'access_token',
    'refresh_token', 'secret', 'api_key', 'apikey', 'credit_card',
    'tarjeta', 'cvv', 'ssn', 'pin', 'otp',
])


class AuditMiddleware:
    """
    Registra peticiones HTTP para trazabilidad de auditoría.
    Sanitiza automáticamente campos sensibles del request body.
    Excluye rutas de assets estáticos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Excluir archivos estáticos y media
        if request.path.startswith(('/static/', '/media/', '/favicon')):
            return self.get_response(request)

        start_time = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Solo loguear peticiones mutadoras o sospechosas
        should_log = (
            request.method in ('POST', 'PUT', 'PATCH', 'DELETE')
            or response.status_code >= 400
        )

        if should_log:
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'ip': self._get_client_ip(request),
                'user': str(getattr(request.user, 'username', 'anonymous')),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                'duration_ms': duration_ms,
            }

            # Sanitizar y agregar request body para POSTs
            if request.method == 'POST' and request.POST:
                log_data['body'] = self._sanitize_body(request.POST)

            if response.status_code >= 400:
                security_logger.warning(
                    "Petición con error: %s", json.dumps(log_data, ensure_ascii=False)
                )
            else:
                audit_logger.info(
                    "Petición: %s", json.dumps(log_data, ensure_ascii=False)
                )

        return response

    def _sanitize_body(self, post_data):
        """
        Sanitiza el cuerpo de la petición eliminando valores de campos
        sensibles (contraseñas, tokens, tarjetas, etc.).
        """
        sanitized = {}
        for key, value in post_data.items():
            if key.lower() in SENSITIVE_FIELDS:
                sanitized[key] = '***REDACTED***'
            elif len(str(value)) > 500:
                sanitized[key] = str(value)[:500] + '...[truncated]'
            else:
                sanitized[key] = str(value)
        return sanitized

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
