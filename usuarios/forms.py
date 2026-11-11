from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
import re

from core.security.validators import validate_email_strict, validate_text_safe
from .models import Usuario


class ValidatingPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError(
                "El correo electrónico ingresado no se encuentra registrado en el sistema."
            )
        return email


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=10,
        required=True,
        error_messages={
            'required': 'Ingresa tu número de documento o código de acceso.',
            'max_length': 'Las credenciales no pueden superar los 10 caracteres.'
        }
    )
    password = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Ingresa tu contraseña secreta.',
            'max_length': 'La contraseña no puede superar los 128 caracteres.'
        }
    )

    def clean_username(self):
        val = self.cleaned_data.get('username', '').strip()
        if not val:
            raise ValidationError("Ingresa tu número de documento o código de acceso.")
        # Detección estricta contra inyección o caracteres prohibidos
        if any(char in val for char in ['<', '>', '"', "'", ';', '--', '/*', '*/']):
            raise ValidationError("Formato de credencial no válido o contiene caracteres no permitidos.")
        # Longitud estricta: Máximo 10 caracteres
        if len(val) > 10:
            raise ValidationError("Las credenciales no pueden superar los 10 caracteres.")
        return val


class RegistroUsuarioForm(forms.Form):
    tipo_documento = forms.ChoiceField(
        choices=Usuario.TIPO_DOC,
        required=True,
        error_messages={
            'required': 'Selecciona tu tipo de documento.',
            'invalid_choice': 'La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista.'
        }
    )
    numero_documento = forms.CharField(
        max_length=10,
        min_length=7,
        required=True,
        error_messages={
            'required': 'El número de documento es obligatorio y debe tener entre 7 y 10 dígitos numéricos.',
            'min_length': 'El número de documento es obligatorio y debe tener entre 7 y 10 dígitos numéricos.',
            'max_length': 'El número de documento es obligatorio y debe tener entre 7 y 10 dígitos numéricos.'
        }
    )
    nombres = forms.CharField(
        max_length=100,
        min_length=2,
        required=True,
        error_messages={
            'required': 'Ingresa tus nombres completos.',
            'min_length': 'Este campo solo permite letras y un máximo de 100 caracteres.',
            'max_length': 'Este campo solo permite letras y un máximo de 100 caracteres.'
        }
    )
    apellidos = forms.CharField(
        max_length=100,
        min_length=2,
        required=True,
        error_messages={
            'required': 'Ingresa tus apellidos completos.',
            'min_length': 'Este campo solo permite letras y un máximo de 100 caracteres.',
            'max_length': 'Este campo solo permite letras y un máximo de 100 caracteres.'
        }
    )
    genero = forms.ChoiceField(
        choices=Usuario.GENERO_CHOICES,
        required=True,
        error_messages={
            'required': 'Selecciona tu género.',
            'invalid_choice': 'La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista.'
        }
    )
    telefono = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        error_messages={
            'required': 'El teléfono debe contener exactamente 10 dígitos numéricos.',
            'min_length': 'El teléfono debe contener exactamente 10 dígitos numéricos.',
            'max_length': 'El teléfono debe contener exactamente 10 dígitos numéricos.'
        }
    )
    programa_formacion = forms.ChoiceField(
        choices=Usuario.PROGRAMA_CHOICES,
        required=True,
        error_messages={
            'required': 'Selecciona tu programa de formación.',
            'invalid_choice': 'La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista.'
        }
    )
    email = forms.EmailField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Ingresa tu correo electrónico.',
            'invalid': 'El correo no tiene un formato válido (ej. usuario@sena.edu.co).',
            'max_length': 'El correo electrónico no puede superar los 100 caracteres.'
        }
    )
    ficha = forms.CharField(
        max_length=7,
        min_length=7,
        required=True,
        error_messages={
            'required': 'La ficha debe contener exactamente 7 dígitos numéricos.',
            'min_length': 'La ficha debe contener exactamente 7 dígitos numéricos.',
            'max_length': 'La ficha debe contener exactamente 7 dígitos numéricos.'
        }
    )
    contrasena = forms.CharField(
        min_length=8,
        max_length=128,
        required=True,
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Ingresa una contraseña.',
            'min_length': 'La contraseña debe tener mínimo 8 caracteres.',
            'max_length': 'La contraseña no puede superar los 128 caracteres.'
        }
    )
    confirmar_contrasena = forms.CharField(
        min_length=8,
        max_length=128,
        required=False,
        widget=forms.PasswordInput
    )

    def clean_numero_documento(self):
        doc = self.cleaned_data.get('numero_documento', '').strip()
        if not re.match(r'^\d{7,10}$', doc):
            raise ValidationError("El número de documento es obligatorio y debe tener entre 7 y 10 dígitos numéricos.")
        if Usuario.objects.filter(numero_documento=doc).exists():
            raise ValidationError("Este número de documento ya se encuentra registrado.")
        return doc

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres', '').strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\'-]+$', nombres):
            raise ValidationError("Este campo solo permite letras y un máximo de 100 caracteres.")
        try:
            return validate_text_safe(nombres, 'nombres', max_length=100).title()
        except ValidationError as e:
            raise ValidationError(str(e.message if hasattr(e, 'message') else e))

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos', '').strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\'-]+$', apellidos):
            raise ValidationError("Este campo solo permite letras y un máximo de 100 caracteres.")
        try:
            return validate_text_safe(apellidos, 'apellidos', max_length=100).title()
        except ValidationError as e:
            raise ValidationError(str(e.message if hasattr(e, 'message') else e))

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if not re.match(r'^\d{10}$', tel):
            raise ValidationError("El teléfono debe contener exactamente 10 dígitos numéricos.")
        return tel

    def clean_ficha(self):
        ficha = self.cleaned_data.get('ficha', '').strip()
        if not re.match(r'^\d{7}$', ficha):
            raise ValidationError("La ficha debe contener exactamente 7 dígitos numéricos.")
        return ficha

    def clean_email(self):
        correo = self.cleaned_data.get('email', '').strip().lower()
        try:
            validate_email_strict(correo)
        except ValidationError as e:
            raise ValidationError(str(e.message if hasattr(e, 'message') else e))
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return correo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('contrasena')
        confirm = cleaned_data.get('confirmar_contrasena')

        if password and confirm and password != confirm:
            self.add_error('confirmar_contrasena', 'Las contraseñas no coinciden.')

        if password:
            temp_user = Usuario(
                username=cleaned_data.get('numero_documento', ''),
                email=cleaned_data.get('email', ''),
                first_name=cleaned_data.get('nombres', ''),
                last_name=cleaned_data.get('apellidos', ''),
                numero_documento=cleaned_data.get('numero_documento', '')
            )
            try:
                validate_password(password, user=temp_user)
            except ValidationError as e:
                self.add_error('contrasena', e.messages[0])

        return cleaned_data

