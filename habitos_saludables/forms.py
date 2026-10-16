"""
forms.py - Formularios del módulo Hábitos Saludables SENA
"""

from django import forms
from django.core.exceptions import ValidationError
from core.security.file_upload import validate_uploaded_file
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
                attrs={'class': 'form-control input-decimal-salud', 'step': '0.1',
                       'min': '20', 'max': '300', 'placeholder': 'Ej: 70.5'}
            ),
            'estatura_cm': forms.NumberInput(
                attrs={'class': 'form-control input-decimal-salud', 'step': '0.1',
                       'min': '100', 'max': '250', 'placeholder': 'Ej: 170'}
            ),
            'presion_sistolica': forms.NumberInput(
                attrs={'class': 'form-control input-entero-estricto', 'min': '40',
                       'max': '260', 'placeholder': 'Ej: 120'}
            ),
            'presion_diastolica': forms.NumberInput(
                attrs={'class': 'form-control input-entero-estricto', 'min': '30',
                       'max': '160', 'placeholder': 'Ej: 80'}
            ),
            'frecuencia_cardiaca': forms.NumberInput(
                attrs={'class': 'form-control input-entero-estricto', 'min': '30',
                       'max': '250', 'placeholder': 'Ej: 72'}
            ),
            'nivel_actividad': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'horas_sueno': forms.NumberInput(
                attrs={'class': 'form-control input-decimal-salud', 'step': '0.5',
                       'min': '0.5', 'max': '24', 'placeholder': 'Ej: 7.5'}
            ),
            'vasos_agua': forms.NumberInput(
                attrs={'class': 'form-control input-entero-estricto', 'min': '1',
                       'max': '50', 'placeholder': 'Ej: 8'}
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
            'estatura_cm': 'Ingresa en centímetros (ej: 170 para 1.70m). Mayor a 0.',
            'presion_sistolica': 'Número más alto al medir la presión (ej: 120)',
            'presion_diastolica': 'Número más bajo al medir la presión (ej: 80)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        hoy = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['fecha_evaluacion'].widget.attrs['min'] = hoy

    def clean_fecha_evaluacion(self):
        fecha = self.cleaned_data.get('fecha_evaluacion')
        from django.utils import timezone
        if fecha and fecha < timezone.localdate():
            raise ValidationError(
                "La fecha de evaluación no puede ser de días anteriores."
            )
        return fecha

    def clean_peso_kg(self):
        peso = self.cleaned_data.get('peso_kg')
        if peso is not None:
            if peso <= 0:
                raise ValidationError("El peso debe ser mayor a 0 kg. No se permiten valores de 0 o negativos.")
            if peso < 20 or peso > 300:
                raise ValidationError("El peso debe estar entre 20 y 300 kg.")
        return peso

    def clean_estatura_cm(self):
        estatura = self.cleaned_data.get('estatura_cm')
        if estatura is not None:
            if estatura <= 0:
                raise ValidationError("La estatura debe ser mayor a 0 cm. No se permiten valores de 0 o negativos.")
            if estatura < 100 or estatura > 250:
                raise ValidationError("La estatura debe estar entre 100 y 250 cm (ej: 170 para 1.70m).")
        return estatura

    def clean_presion_sistolica(self):
        sistolica = self.cleaned_data.get('presion_sistolica')
        if sistolica is not None:
            if sistolica <= 0:
                raise ValidationError("La presión sistólica debe ser mayor a 0 mmHg. No se permiten valores de 0 o negativos.")
            if sistolica < 40 or sistolica > 260:
                raise ValidationError("La presión sistólica debe estar en un rango válido entre 40 y 260 mmHg.")
        return sistolica

    def clean_presion_diastolica(self):
        diastolica = self.cleaned_data.get('presion_diastolica')
        if diastolica is not None:
            if diastolica <= 0:
                raise ValidationError("La presión diastólica debe ser mayor a 0 mmHg. No se permiten valores de 0 o negativos.")
            if diastolica < 30 or diastolica > 160:
                raise ValidationError("La presión diastólica debe estar en un rango válido entre 30 y 160 mmHg.")
        return diastolica

    def clean_frecuencia_cardiaca(self):
        fc = self.cleaned_data.get('frecuencia_cardiaca')
        if fc is not None:
            if fc <= 0:
                raise ValidationError("La frecuencia cardíaca debe ser mayor a 0 lpm. No se permiten valores de 0 o negativos.")
            if fc < 30 or fc > 250:
                raise ValidationError("La frecuencia cardíaca debe estar entre 30 y 250 lpm.")
        return fc

    def clean_horas_sueno(self):
        horas = self.cleaned_data.get('horas_sueno')
        if horas is not None:
            if horas <= 0:
                raise ValidationError("Las horas de sueño deben ser mayores a 0. No se permiten valores de 0 o negativos.")
            if horas < 0.5 or horas > 24:
                raise ValidationError("Las horas de sueño deben estar entre 0.5 y 24 horas diarias.")
        return horas

    def clean_vasos_agua(self):
        vasos = self.cleaned_data.get('vasos_agua')
        if vasos is not None:
            if vasos <= 0:
                raise ValidationError("El número de vasos de agua debe ser mayor a 0. No se permiten valores de 0 o negativos.")
            if vasos > 50:
                raise ValidationError("El número de vasos de agua no puede superar 50 vasos al día.")
        return vasos

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
        # Validar tipo/size/magic-bytes del archivo subido
        if archivo:
            try:
                validate_uploaded_file(archivo, allowed_types="document")
            except ValidationError:
                self.add_error(
                    'archivo',
                    'Tipo de archivo no permitido o archivo inválido.')
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
