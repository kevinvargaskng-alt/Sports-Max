"""
core/security/webhook_validator.py
Validación criptográfica de webhooks entrantes:
firma HMAC-SHA256 y validación de timestamp anti-replay.
"""

import hmac
import hashlib
import time
import logging
from django.conf import settings

security_logger = logging.getLogger('security')

# Máxima antigüedad permitida de un webhook (5 minutos)
MAX_WEBHOOK_AGE_SECONDS = 300


def validate_webhook_signature(request, secret_key=None, header_signature='X-Signature',
                                header_timestamp='X-Timestamp'):
    """
    Valida la firma HMAC-SHA256 y el timestamp de un webhook entrante.

    Args:
        request: HttpRequest de Django
        secret_key: Clave secreta para HMAC (default: settings.WEBHOOK_SECRET)
        header_signature: Nombre del header con la firma
        header_timestamp: Nombre del header con el timestamp

    Returns:
        (True, None) si la validación pasa
        (False, str) con razón del fallo

    Uso:
        valid, error = validate_webhook_signature(request)
        if not valid:
            return JsonResponse({'error': error}, status=401)
    """
    webhook_secret = secret_key or getattr(settings, 'WEBHOOK_SECRET', None)
    if not webhook_secret:
        security_logger.error("WEBHOOK_SECRET no configurado en settings.py")
        return False, "Configuración de webhook incompleta."

    # 1. Verificar que los headers requeridos estén presentes
    signature = request.headers.get(header_signature, '')
    timestamp_str = request.headers.get(header_timestamp, '')

    if not signature:
        security_logger.warning(
            "Webhook sin firma: path=%s ip=%s",
            request.path, _get_ip(request)
        )
        return False, "Firma del webhook no proporcionada."

    if not timestamp_str:
        security_logger.warning(
            "Webhook sin timestamp: path=%s ip=%s",
            request.path, _get_ip(request)
        )
        return False, "Timestamp del webhook no proporcionado."

    # 2. Validar timestamp (anti-replay)
    try:
        webhook_timestamp = int(timestamp_str)
        current_time = int(time.time())
        age = abs(current_time - webhook_timestamp)

        if age > MAX_WEBHOOK_AGE_SECONDS:
            security_logger.warning(
                "Webhook rechazado por timestamp: age=%ds max=%ds path=%s ip=%s",
                age, MAX_WEBHOOK_AGE_SECONDS, request.path, _get_ip(request)
            )
            return False, "Webhook expirado (timestamp demasiado antiguo)."

    except (ValueError, TypeError):
        return False, "Timestamp del webhook inválido."

    # 3. Calcular HMAC-SHA256 esperado
    payload = request.body or b''
    message = f"{timestamp_str}.".encode('utf-8') + payload
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()

    # 4. Comparación segura contra timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        security_logger.warning(
            "Webhook con firma inválida: path=%s ip=%s",
            request.path, _get_ip(request)
        )
        return False, "Firma del webhook inválida."

    return True, None


def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
