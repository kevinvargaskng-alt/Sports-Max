"""
core/security/encryption.py
Cifrado de datos PII en reposo usando Fernet (AES-128-CBC).
Proporciona un EncryptedCharField para usar en modelos Django.
"""

import base64
import hashlib
from django.conf import settings
from django.db import models

try:
    from cryptography.fernet import Fernet, InvalidToken
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def _get_fernet_key():
    """
    Deriva una clave Fernet a partir del SECRET_KEY de Django.
    Fernet requiere una clave de 32 bytes codificada en base64.
    """
    key_material = settings.SECRET_KEY.encode('utf-8')
    # Derivar 32 bytes usando SHA-256
    key_hash = hashlib.sha256(key_material).digest()
    return base64.urlsafe_b64encode(key_hash)


def _get_fernet():
    """Obtiene la instancia Fernet con la clave derivada."""
    if not HAS_CRYPTOGRAPHY:
        return None
    return Fernet(_get_fernet_key())


def encrypt_value(plaintext):
    """Cifra un valor de texto plano. Retorna string cifrado base64."""
    if not plaintext:
        return plaintext

    fernet = _get_fernet()
    if fernet is None:
        return plaintext  # Fallback: sin cifrar si cryptography no instalado

    return fernet.encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_value(ciphertext):
    """Descifra un valor cifrado. Retorna el texto plano original."""
    if not ciphertext:
        return ciphertext

    fernet = _get_fernet()
    if fernet is None:
        return ciphertext

    try:
        return fernet.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except (InvalidToken, Exception):
        # Si falla el descifrado (clave cambiada, dato no cifrado),
        # retornar el valor original como fallback
        return ciphertext


def hash_for_search(value):
    """
    Genera un hash determinístico para búsquedas de campos cifrados.
    Permite buscar por email/documento sin descifrar todos los registros.
    """
    if not value:
        return ''
    normalized = value.strip().lower()
    return hashlib.sha256(
        (normalized + settings.SECRET_KEY[:16]).encode('utf-8')
    ).hexdigest()
