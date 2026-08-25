"""
core/security/password_validators.py
Validadores de contraseña robustos: lista de contraseñas comprometidas,
complejidad mínima y prevención de patrones débiles.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


# Top contraseñas comprometidas/filtradas más comunes (extendida)
BREACHED_PASSWORDS = frozenset([
    'password', 'password1', 'password123', '123456', '12345678',
    '123456789', '1234567890', 'qwerty', 'qwerty123', 'abc123',
    'monkey', 'master', 'dragon', 'login', 'princess', 'football',
    'shadow', 'sunshine', 'trustno1', 'iloveyou', 'batman', 'access',
    'hello', 'charlie', 'donald', '123123', '654321', '666666',
    '111111', '000000', '121212', 'qwertyuiop', 'admin', 'admin123',
    'root', 'toor', 'letmein', 'welcome', 'welcome1', 'passw0rd',
    'p@ssw0rd', 'p@ssword', 'contrasena', 'contraseña', '12341234',
    'abcdefgh', 'abc12345', '11111111', '00000000', 'michael',
    'jordan23', 'hunter', 'hunter2', 'mustang', 'jennifer',
    'baseball', 'soccer', 'harley', 'ranger', 'thomas', 'klaster',
    'george', 'computer', 'michelle', 'jessica', 'pepper', 'zxcvbn',
    'zxcvbnm', '1q2w3e', '1q2w3e4r', '1qaz2wsx', 'qazwsx',
    'starwars', 'solo', 'summer', 'flower', 'buster', 'matrix',
    'whatever', 'sena2024', 'sena2025', 'sena2026', 'sena1234',
    'colombia', 'bogota', 'deportes', 'futbol', 'gimnasio',
])


class BreachedPasswordValidator:
    """
    Rechaza contraseñas que aparezcan en la lista de las más filtradas
    a nivel global. Previene ataques de diccionario.
    """

    def validate(self, password, user=None):
        if password.lower().strip() in BREACHED_PASSWORDS:
            raise ValidationError(
                _("Esta contraseña ha sido comprometida en filtraciones de datos "
                  "conocidas. Elige una contraseña más segura y única."),
                code='breached_password',
            )

    def get_help_text(self):
        return _(
            "Tu contraseña no puede ser una de las contraseñas más "
            "comúnmente usadas o filtradas."
        )


class StrongPasswordValidator:
    """
    Exige complejidad: mayúscula, minúscula, dígito y carácter especial.
    Longitud mínima de 12 caracteres.
    """

    def __init__(self, min_length=12):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("La contraseña debe tener al menos %(min_length)d caracteres."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code='password_no_lower',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            raise ValidationError(
                _("La contraseña debe incluir al menos un carácter especial "
                  "(ej: @, #, $, !, etc.)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            "Tu contraseña debe tener al menos %(min_length)d caracteres, "
            "incluyendo mayúsculas, minúsculas, números y caracteres especiales."
        ) % {'min_length': self.min_length}


class NoPersonalInfoValidator:
    """
    Impide que la contraseña contenga datos personales del usuario
    (documento, email username, nombre, apellido).
    """

    def validate(self, password, user=None):
        if user is None:
            return

        pwd_lower = password.lower()

        # Campos a comparar
        fields_to_check = []
        if hasattr(user, 'numero_documento') and user.numero_documento:
            fields_to_check.append(user.numero_documento)
        if hasattr(user, 'username') and user.username:
            fields_to_check.append(user.username)
        if hasattr(user, 'first_name') and user.first_name:
            fields_to_check.append(user.first_name)
        if hasattr(user, 'last_name') and user.last_name:
            fields_to_check.append(user.last_name)
        if hasattr(user, 'email') and user.email:
            email_user = user.email.split('@')[0]
            if len(email_user) >= 3:
                fields_to_check.append(email_user)

        for field_value in fields_to_check:
            if len(field_value) >= 3 and field_value.lower() in pwd_lower:
                raise ValidationError(
                    _("La contraseña no puede contener información personal "
                      "(nombre, apellido, documento o correo)."),
                    code='password_contains_personal_info',
                )

    def get_help_text(self):
        return _(
            "Tu contraseña no puede contener tu nombre, apellido, "
            "número de documento ni tu correo electrónico."
        )
