"""
core/security/validators.py
Validadores basados en esquemas para todas las entradas de usuario.
Asume que TODA entrada del cliente es potencialmente maliciosa.
"""

import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email


# ─── Dominios de email desechables conocidos ──────────────────────
DISPOSABLE_DOMAINS = frozenset([
    'tempmail.com', 'throwaway.email', 'guerrillamail.com', 'mailinator.com',
    'yopmail.com', 'trashmail.com', 'sharklasers.com', 'guerrillamailblock.com',
    'grr.la', 'dispostable.com', 'maildrop.cc', 'tempail.com', '10minutemail.com',
    'temp-mail.org', 'fakeinbox.com', 'tempmailo.com', 'mohmal.com',
])

# ─── Dominios institucionales permitidos (SENA + comunes Colombia) ───
ALLOWED_EMAIL_DOMAINS = [
    'sena.edu.co', 'misena.edu.co', 'gmail.com', 'outlook.com',
    'hotmail.com', 'yahoo.com', 'live.com', 'icloud.com',
]


def validate_email_strict(email):
    """
    Validación estricta de correo electrónico:
    1. Formato RFC 5322 (vía Django)
    2. Dominio no desechable
    3. Longitud máxima
    """
    if not email or len(email) > 254:
        raise ValidationError("Correo electrónico inválido o demasiado largo.")

    # Validación de formato Django
    django_validate_email(email)

    # Extraer dominio
    domain = email.rsplit('@', 1)[-1].lower()

    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError(
            "No se permiten correos electrónicos temporales/desechables. "
            "Usa un correo institucional o personal válido."
        )

    return email


def validate_text_safe(value, field_name='campo', max_length=500):
    """
    Valida texto libre contra inyección de scripts y longitud excesiva.
    """
    if not value:
        return value

    value = str(value).strip()

    if len(value) > max_length:
        raise ValidationError(
            f"El {field_name} excede la longitud máxima de {max_length} caracteres."
        )

    # Detectar patrones de inyección comunes
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
        r'\.innerHTML',
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                f"El {field_name} contiene contenido no permitido."
            )

    return value


def validate_numeric_id(value, field_name='ID'):
    """Valida que un valor sea un entero positivo (para IDs internos)."""
    try:
        int_val = int(value)
        if int_val <= 0:
            raise ValueError
        return int_val
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} inválido.")


# ═══════════════════════════════════════════════════════════
#  FORMULARIOS DE VALIDACIÓN (Schema-based)
# ═══════════════════════════════════════════════════════════

class RegistroForm(forms.Form):
    """Validación basada en esquema para el formulario de registro."""
    numero_documento = forms.CharField(
        min_length=5, max_length=20,
        validators=[
            forms.RegexField(regex=r'^\d{5,20}$', error_messages={
                'invalid': 'El documento debe contener solo números (5-20 dígitos).'
            }).validators[0]
        ]
    )
    nombres = forms.CharField(min_length=2, max_length=100)
    apellidos = forms.CharField(min_length=2, max_length=100)
    contrasena = forms.CharField(min_length=12, max_length=128)
    email = forms.EmailField(max_length=254)
    tipo_documento = forms.ChoiceField(choices=[
        ('CC', 'CC'), ('TI', 'TI'), ('CE', 'CE'), ('PA', 'PA'),
    ])
    telefono = forms.CharField(max_length=15, required=False)
    ficha = forms.CharField(max_length=20, required=False)
    programa_formacion = forms.CharField(max_length=25, required=False)
    genero = forms.ChoiceField(choices=[
        ('M', 'M'), ('F', 'F'), ('O', 'O'), ('NR', 'NR'),
    ])

    def clean_email(self):
        return validate_email_strict(self.cleaned_data['email'])

    def clean_nombres(self):
        return validate_text_safe(
            self.cleaned_data['nombres'], 'nombre', max_length=100
        ).title()

    def clean_apellidos(self):
        return validate_text_safe(
            self.cleaned_data['apellidos'], 'apellidos', max_length=100
        ).title()


class PerfilUpdateForm(forms.Form):
    """Validación para actualización de perfil (whitelist de campos)."""
    email = forms.EmailField(max_length=254, required=False)
    celular = forms.CharField(max_length=15, required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return validate_email_strict(email)
        return email

    def clean_celular(self):
        celular = self.cleaned_data.get('celular', '').strip()
        if celular and not re.match(r'^\+?\d{7,15}$', celular):
            raise ValidationError("Número de teléfono inválido.")
        return celular


class PrestamoForm(forms.Form):
    """Validación para solicitud de préstamo."""
    elemento = forms.IntegerField(min_value=1)
    cantidad_prestada = forms.IntegerField(min_value=1, max_value=50)
    dias_prestamo = forms.IntegerField(min_value=1, max_value=15)
    observacion = forms.CharField(max_length=500, required=False)

    def clean_observacion(self):
        return validate_text_safe(
            self.cleaned_data.get('observacion', ''),
            'observación',
            max_length=500,
        )


class ElementoDeportivoForm(forms.Form):
    """Validación para crear/editar elementos deportivos (admin)."""
    nombre_elemento = forms.CharField(min_length=2, max_length=100)
    cantidad_total = forms.IntegerField(min_value=0, max_value=9999)
    descripcion = forms.CharField(max_length=1000, required=False)
    usuario_responsable = forms.IntegerField(required=False)

    def clean_nombre_elemento(self):
        return validate_text_safe(
            self.cleaned_data['nombre_elemento'],
            'nombre del elemento',
            max_length=100,
        )

    def clean_descripcion(self):
        return validate_text_safe(
            self.cleaned_data.get('descripcion', ''),
            'descripción',
            max_length=1000,
        )


class SugerenciaForm(forms.Form):
    """Validación para el buzón de sugerencias."""
    tipo = forms.ChoiceField(
        choices=[
            ('otro', 'otro'), ('error', 'error'), ('sugerencia', 'sugerencia'),
            ('mejora', 'mejora'), ('queja', 'queja'),
        ],
        required=False,
    )
    comentario = forms.CharField(min_length=10, max_length=2000)

    def clean_comentario(self):
        return validate_text_safe(
            self.cleaned_data['comentario'],
            'comentario',
            max_length=2000,
        )
