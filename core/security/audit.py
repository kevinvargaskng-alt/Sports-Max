"""
core/security/audit.py
Sistema de auditoría centralizado para eventos de seguridad.
Registra login, acciones admin y peticiones sospechosas con
sanitización automática de datos sensibles.
"""

import json
import logging
from datetime import datetime
from django.utils import timezone

security_logger = logging.getLogger('security')
audit_logger = logging.getLogger('audit')

# Campos cuyo valor se oculta al loguear
REDACTED_FIELDS = frozenset([
    'password', 'contrasena', 'contraseña', 'token', 'access_token',
    'refresh_token', 'secret', 'api_key', 'credit_card', 'tarjeta',
    'cvv', 'pin', 'otp', 'secret_key',
])


def _get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _sanitize_dict(data):
    """Redacta valores sensibles de un diccionario."""
    sanitized = {}
    for key, value in data.items():
        if key.lower() in REDACTED_FIELDS:
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, str) and len(value) > 200:
            sanitized[key] = value[:200] + '...'
        else:
            sanitized[key] = str(value)
    return sanitized


def log_login_attempt(request, username, success, reason=''):
    """
    Registra intentos de inicio de sesión (exitosos y fallidos).
    """
    event = {
        'event': 'LOGIN_ATTEMPT',
        'timestamp': timezone.now().isoformat(),
        'username': username,
        'success': success,
        'ip': _get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
    }
    if reason:
        event['reason'] = reason

    if success:
        audit_logger.info("Login exitoso: %s", json.dumps(event, ensure_ascii=False))
    else:
        security_logger.warning(
            "Login fallido: %s", json.dumps(event, ensure_ascii=False)
        )


def log_admin_action(request, action, target_model='', target_id='', details=''):
    """
    Registra acciones administrativas para trazabilidad en archivo y base de datos (CP-02).
    """
    admin_user = getattr(request, 'user', None)
    admin_username = getattr(admin_user, 'username', 'unknown')
    ip = _get_client_ip(request)

    event = {
        'event': 'ADMIN_ACTION',
        'timestamp': timezone.now().isoformat(),
        'admin': admin_username,
        'action': action,
        'target': f"{target_model}#{target_id}" if target_id else target_model,
        'ip': ip,
    }
    if details:
        event['details'] = str(details)[:500]

    audit_logger.info(
        "Acción admin: %s", json.dumps(event, ensure_ascii=False)
    )

    # ── CP-02: Guardado automático en la tabla historial_acciones ──
    try:
        from usuarios.models import HistorialAccion
        user_obj = admin_user if (admin_user and admin_user.is_authenticated) else None
        HistorialAccion.objects.create(
            usuario=user_obj,
            modulo=target_model or 'General',
            accion=action,
            descripcion=f"{target_id}: {details}" if target_id else (details or action),
            ip_origen=ip
        )
    except Exception as e:
        security_logger.error("Error guardando en historial_acciones: %s", e)



def log_suspicious_request(request, reason):
    """
    Registra peticiones sospechosas (posibles ataques, acceso no autorizado, etc.).
    """
    event = {
        'event': 'SUSPICIOUS_REQUEST',
        'timestamp': timezone.now().isoformat(),
        'reason': reason,
        'method': request.method,
        'path': request.path,
        'ip': _get_client_ip(request),
        'user': str(getattr(request.user, 'username', 'anonymous')),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
    }

    # Incluir body sanitizado si es POST
    if request.method == 'POST' and request.POST:
        event['body'] = _sanitize_dict(request.POST)

    security_logger.warning(
        "Petición sospechosa: %s", json.dumps(event, ensure_ascii=False)
    )


def log_security_event(event_type, message, extra=None):
    """
    Registra un evento de seguridad genérico.
    """
    event = {
        'event': event_type,
        'timestamp': timezone.now().isoformat(),
        'message': message,
    }
    if extra:
        event.update(extra)

    security_logger.warning(
        "Evento de seguridad: %s", json.dumps(event, ensure_ascii=False)
    )
