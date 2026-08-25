"""
core/security/file_upload.py
Validación segura de archivos subidos: magic bytes, extensiones,
tamaño máximo y renombrado con hash aleatorio.
"""

import uuid
import os
import logging
from django.core.exceptions import ValidationError

security_logger = logging.getLogger('security')


# ─── Firmas de archivo (magic bytes) ─────────────────────────────
FILE_SIGNATURES = {
    # Imágenes
    b'\xff\xd8\xff': {'extensions': ['.jpg', '.jpeg'], 'mime': 'image/jpeg'},
    b'\x89PNG\r\n\x1a\n': {'extensions': ['.png'], 'mime': 'image/png'},
    b'GIF87a': {'extensions': ['.gif'], 'mime': 'image/gif'},
    b'GIF89a': {'extensions': ['.gif'], 'mime': 'image/gif'},
    b'RIFF': {'extensions': ['.webp'], 'mime': 'image/webp'},  # RIFF...WEBP

    # Documentos
    b'%PDF': {'extensions': ['.pdf'], 'mime': 'application/pdf'},
}

# ─── Configuración de límites ─────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = frozenset(['.jpg', '.jpeg', '.png', '.gif', '.webp'])
ALLOWED_DOCUMENT_EXTENSIONS = frozenset(['.pdf', '.doc', '.docx', '.pptx', '.xlsx'])
ALL_ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_uploaded_file(uploaded_file, allowed_types='image', max_size=None):
    """
    Validación completa de archivo subido:
    1. Verifica extensión contra whitelist
    2. Verifica tamaño máximo
    3. Inspecciona magic bytes (file signature)
    4. Renombra con UUID aleatorio

    Args:
        uploaded_file: InMemoryUploadedFile o TemporaryUploadedFile
        allowed_types: 'image', 'document', o 'all'
        max_size: Tamaño máximo en bytes (None = usar default)

    Returns:
        uploaded_file con nombre sanitizado

    Raises:
        ValidationError si el archivo no pasa la validación
    """
    if uploaded_file is None:
        return None

    # 1. Verificar extensión
    original_name = uploaded_file.name or ''
    ext = os.path.splitext(original_name)[1].lower()

    if allowed_types == 'image':
        allowed_ext = ALLOWED_IMAGE_EXTENSIONS
        default_max = MAX_IMAGE_SIZE
    elif allowed_types == 'document':
        allowed_ext = ALLOWED_DOCUMENT_EXTENSIONS
        default_max = MAX_DOCUMENT_SIZE
    else:
        allowed_ext = ALL_ALLOWED_EXTENSIONS
        default_max = MAX_DOCUMENT_SIZE

    if ext not in allowed_ext:
        security_logger.warning(
            "Archivo rechazado por extensión: nombre=%s ext=%s",
            original_name, ext
        )
        raise ValidationError(
            f"Tipo de archivo no permitido ({ext}). "
            f"Extensiones válidas: {', '.join(sorted(allowed_ext))}"
        )

    # 2. Verificar tamaño
    effective_max = max_size or default_max
    if uploaded_file.size > effective_max:
        max_mb = effective_max / (1024 * 1024)
        security_logger.warning(
            "Archivo rechazado por tamaño: nombre=%s size=%d max=%d",
            original_name, uploaded_file.size, effective_max
        )
        raise ValidationError(
            f"El archivo excede el tamaño máximo de {max_mb:.0f} MB."
        )

    # 3. Verificar magic bytes (file signature)
    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(16)
        uploaded_file.seek(0)

        if header and ext in ALLOWED_IMAGE_EXTENSIONS:
            magic_valid = False
            for signature, info in FILE_SIGNATURES.items():
                if header.startswith(signature):
                    if ext in info['extensions']:
                        magic_valid = True
                        break
                    else:
                        # Extensión no coincide con el magic byte
                        security_logger.warning(
                            "Archivo rechazado: extensión %s no coincide con firma %s "
                            "(nombre=%s)",
                            ext, info['mime'], original_name
                        )
                        raise ValidationError(
                            "El contenido del archivo no coincide con su extensión. "
                            "Posible archivo malicioso."
                        )

            # Caso especial: WebP tiene header RIFF...WEBP
            if ext == '.webp' and not magic_valid:
                if header[:4] == b'RIFF' and len(header) >= 12 and header[8:12] == b'WEBP':
                    magic_valid = True

            if not magic_valid and ext in ALLOWED_IMAGE_EXTENSIONS:
                security_logger.warning(
                    "Archivo rechazado: firma no reconocida para ext=%s (nombre=%s)",
                    ext, original_name
                )
                raise ValidationError(
                    "No se pudo verificar el tipo real del archivo. "
                    "Asegúrate de subir una imagen válida."
                )
    except ValidationError:
        raise
    except Exception as e:
        security_logger.error("Error verificando magic bytes: %s", e)

    # 4. Renombrar con UUID aleatorio (previene path traversal y sobreescritura)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    uploaded_file.name = safe_name

    return uploaded_file


def generate_secure_filename(original_name):
    """
    Genera un nombre de archivo seguro basado en UUID.
    Preserva solo la extensión original.
    """
    ext = os.path.splitext(original_name or '')[1].lower()
    if ext not in ALL_ALLOWED_EXTENSIONS:
        ext = ''
    return f"{uuid.uuid4().hex}{ext}"
