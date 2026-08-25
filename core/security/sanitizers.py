"""
core/security/sanitizers.py
Sanitización de contenido HTML y texto generado por el usuario
para prevenir XSS almacenado (Stored XSS).
"""

import re
import html


def sanitize_html(text):
    """
    Sanitiza texto que pueda contener HTML malicioso.
    Escapa todas las entidades HTML y elimina tags peligrosos.

    Para campos de texto libre (comentarios, descripciones, observaciones).
    No usa bibliotecas externas — implementación pura Python segura.
    """
    if not text:
        return text

    text = str(text)

    # 1. Escapar todas las entidades HTML
    text = html.escape(text, quote=True)

    return text


def sanitize_input(text, max_length=5000):
    """
    Sanitización de entrada genérica:
    1. Strip de whitespace
    2. Eliminación de caracteres de control (excepto newlines y tabs)
    3. Limitación de longitud
    4. Normalización de whitespace excesivo
    """
    if not text:
        return text

    text = str(text).strip()

    # Eliminar caracteres de control (excepto \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Normalizar whitespace excesivo (múltiples espacios → uno)
    text = re.sub(r' {3,}', '  ', text)

    # Limitar newlines consecutivos
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Truncar si excede longitud máxima
    if len(text) > max_length:
        text = text[:max_length]

    return text


def strip_dangerous_patterns(text):
    """
    Elimina patrones específicos de inyección de la entrada.
    Para campos donde se necesita ser extra cauteloso.
    """
    if not text:
        return text

    text = str(text)

    # Remover patrones de inyección de script
    patterns_to_remove = [
        r'<script[^>]*>.*?</script>',
        r'javascript\s*:',
        r'on\w+\s*=\s*["\']',
        r'<\s*iframe',
        r'<\s*object',
        r'<\s*embed',
        r'<\s*form',
        r'<\s*input',
        r'expression\s*\(',
        r'url\s*\(\s*["\']?\s*javascript',
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()
