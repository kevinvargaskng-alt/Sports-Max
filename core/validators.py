import re
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

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
    MaxValueValidator(250.00, message="El peso máximo permitido es de 250.00 kg.")
]

validador_estatura_salud = [
    MinValueValidator(1.00, message="La estatura mínima permitida es de 1.00 m."),
    MaxValueValidator(2.50, message="La estatura máxima permitida es de 2.50 m.")
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
