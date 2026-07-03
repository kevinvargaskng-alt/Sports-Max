from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

class ValidatingPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError(
                "El correo electrónico ingresado no se encuentra registrado en el sistema."
            )
        return email
