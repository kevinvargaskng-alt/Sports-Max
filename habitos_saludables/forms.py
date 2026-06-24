"""
forms.py - Formularios del módulo Hábitos Saludables SENA
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import (
    SeguimientoSalud, MaterialApoyo, PiramideNutricional,
    HabitoSaludable, RutinaFisica, HabeasDataConsent
)


class HabeasDataForm(forms.ModelForm):
    """
    Formulario de aceptación obligatoria de Habeas Data.
    Debe completarse antes de registrar información médica.
    """
    acepta = forms.BooleanField(
        required=True,
        label='Acepto el tratamiento de mis datos personales conforme a la '
              'Ley 1581 de 2012 y la política de privacidad del SENA.',
        error_messages={
            'required': 'Debes aceptar el tratamiento de datos para continuar.'
        }
    )

    class Meta:
        model = HabeasDataConsent
        fields = ['acepta']

    def clean_acepta(self):
        valor = self.cleaned_data.get('acepta')
        if not valor:
            raise ValidationError(
                'La aceptación del Habeas Data es obligatoria para '
                'registrar información de salud.'
            )
        return valor


class SeguimientoSaludForm(forms.ModelForm):
    """
    Registro de indicadores de salud. Calcula IMC automáticamente.
    Requiere Habeas Data aceptado.
    """
    class Meta:
        model = SeguimientoSalud
        fields = [
            'fecha_evaluacion', 'peso_kg', 'estatura_cm',
            'presion_sistolica', 'presion_diastolica',
            'frecuencia_cardiaca', 'nivel_actividad',
            'horas_sueno', 'vasos_agua', 'observaciones'
        ]
        widgets = {
            'fecha_evaluacion': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'peso_kg': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.1',
                       'placeholder': 'Ej: 70.5'}
            ),
            'estatura_cm': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.1',
                       'placeholder': 'Ej: 170'}
            ),
            'presion_sistolica': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: 120'}
            ),
            'presion_diastolica': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: 80'}
            ),
            'frecuencia_cardiaca': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: 72'}
            ),
            'nivel_actividad': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'horas_sueno': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.5',
                       'placeholder': 'Ej: 7.5'}
            ),
            'vasos_agua': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: 8'}
            ),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3,
                       'placeholder': 'Notas adicionales sobre tu salud...'}
            ),
        }
        labels = {
            'peso_kg': 'Peso actual (kg)',
            'estatura_cm': 'Estatura (cm)',
            'presion_sistolica': 'Presión sistólica (mmHg)',
            'presion_diastolica': 'Presión diastólica (mmHg)',
            'frecuencia_cardiaca': 'Frecuencia cardíaca (lpm)',
            'horas_sueno': 'Horas de sueño promedio',
            'vasos_agua': 'Vasos de agua al día (250ml)',
        }
        help_texts = {
            'estatura_cm': 'Ingresa en centímetros (ej: 170 para 1.70m)',
            'presion_sistolica': 'Número más alto al medir la presión',
            'presion_diastolica': 'Número más bajo al medir la presión',
        }

    def clean(self):
        cleaned = super().clean()
        sistolica = cleaned.get('presion_sistolica')
        diastolica = cleaned.get('presion_diastolica')

        # Validar que sistólica sea mayor que diastólica
        if sistolica and diastolica:
            if sistolica <= diastolica:
                raise ValidationError(
                    'La presión sistólica debe ser mayor que la diastólica.'
                )

        return cleaned


class MaterialApoyoForm(forms.ModelForm):
    """Formulario para subir material de apoyo (admin/instructor)."""
    class Meta:
        model = MaterialApoyo
        fields = [
            'titulo', 'descripcion', 'tipo_contenido',
            'archivo', 'url_video', 'imagen_portada',
            'autor', 'fecha_publicacion', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_contenido': forms.Select(attrs={'class': 'form-select'}),
            'url_video': forms.URLInput(attrs={'class': 'form-control',
                                               'placeholder': 'https://youtube.com/...'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date',
                                                        'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_contenido')
        archivo = cleaned.get('archivo')
        url_video = cleaned.get('url_video')

        if tipo == 'video' and not url_video:
            raise ValidationError(
                'Para tipo "Video" debes ingresar la URL del video.'
            )
        if tipo in ('pdf', 'documento', 'presentacion') and not archivo:
            raise ValidationError(
                f'Para tipo "{tipo}" debes adjuntar un archivo.'
            )
        return cleaned


class BuscarMaterialForm(forms.Form):
    """Formulario de búsqueda/filtro para la biblioteca."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar material...'
        })
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + MaterialApoyo.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
