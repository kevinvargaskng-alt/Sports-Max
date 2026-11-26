import re
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.html import strip_tags


# Validadores comunes para formularios, modelos y vistas que reciben POST.
LETRAS_ESPACIOS_REGEX = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$'
ALFANUMERICO_GUION_REGEX = r'^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$'

validador_solo_letras = RegexValidator(
    regex=LETRAS_ESPACIOS_REGEX,
    message='El campo solo puede contener letras y espacios.'
)
validador_documento = RegexValidator(
    regex=r'^\d{6,10}$',
    message='El documento debe contener entre 6 y 10 dígitos.'
)
validador_telefono_colombiano = RegexValidator(
    regex=r'^3\d{9}$',
    message='El teléfono debe tener 10 dígitos y comenzar por 3.'
)
validador_digitos = RegexValidator(
    regex=r'^\d+$',
    message='Este campo solo puede contener dígitos.'
)
validador_alfanumerico_guion = RegexValidator(
    regex=ALFANUMERICO_GUION_REGEX,
    message='Use solo letras, números y guiones, sin espacios ni símbolos.'
)
# REVISAR: nombres de implementos/equipos pueden incluir números de modelo.
validador_nombre_con_numeros = RegexValidator(
    regex=r'^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+(?:[ \-][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+)*$',
    message='Use letras, números, espacios y guiones.'
)


def normalizar_espacios(value):
    """Recorta extremos y deja un solo espacio entre palabras."""
    return ' '.join(str(value or '').split())


def validar_letras(value):
    value = normalizar_espacios(value)
    if not value or not re.fullmatch(LETRAS_ESPACIOS_REGEX, value):
        raise ValidationError('El campo solo puede contener letras y espacios.')
    return value


def limpiar_texto_largo(value, max_length=2000, field_name='texto'):
    """Quita etiquetas HTML y scripts; normaliza y limita texto libre."""
    value = str(value or '')
    value = re.sub(r'<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>', ' ', value,
                   flags=re.IGNORECASE | re.DOTALL)
    value = '\n'.join(' '.join(line.split()) for line in strip_tags(value).splitlines()).strip()
    if len(value) > max_length:
        raise ValidationError(f'{field_name.capitalize()} no puede superar {max_length} caracteres.')
    return value

# 1. 🚫 Validador de texto sin caracteres especiales
validador_texto_limpio = RegexValidator(
    regex=r'^[^@#$%&*=\/\\<>!¡?¿^{}\[\]~|]+$',
    message="No se permiten caracteres especiales (@, #, $, %, &, *, =, /, \\, <, >, etc.) en este campo."
)

# 2. 🔢 Validador de enteros estrictos (positivos)
validador_entero_positivo = RegexValidator(
    regex=r'^\d+$',
    message="Este campo solo acepta números enteros positivos."
)

# 3. 📏 Validadores de medidas de salud y rangos biológicos humanos
validador_peso_salud = [
    MinValueValidator(30.00, message="El peso mínimo permitido es de 30.00 kg."),
    MaxValueValidator(200.00, message="El peso máximo permitido es de 200.00 kg.")
]

validador_estatura_salud = [
    MinValueValidator(1.00, message="La estatura mínima permitida es de 1.00 m."),
    MaxValueValidator(2.30, message="La estatura máxima permitida es de 2.30 m.")
]

# 4. 🔐 Validador de contraseña segura
def validador_password_segura(value):
    if not re.search(r'[A-Z]', value):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r'\d', value):
        raise ValidationError("La contraseña debe contener al menos un número.")
    if not re.search(r'[@#$%^&+=!._-]', value):
        raise ValidationError("La contraseña debe incluir al menos un carácter especial.")

# 5. 📅 Validador de fecha no pasada y máximo 7 días a futuro
def validador_fecha_futura_7dias(value):
    if not value:
        return
    hoy = date.today()
    max_fecha = hoy + timedelta(days=7)
    if value < hoy:
        raise ValidationError("No se permiten fechas anteriores al día de hoy.")
    if value > max_fecha:
        raise ValidationError("Las reservas solo se permiten con un máximo de 7 días de anticipación.")
