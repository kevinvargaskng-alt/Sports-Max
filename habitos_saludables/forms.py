"""
forms.py - Formularios del módulo Hábitos Saludables SENA
"""

from django import forms
from django.core.exceptions import ValidationError
from core.security.file_upload import validate_uploaded_file
from core.validators import limpiar_texto_largo
from .models import (
    SeguimientoSalud, MaterialApoyo, PiramideNutricional,
    HabitoSaludable, RutinaFisica, HabeasDataConsent, RecetaSaludable
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
                       'min': '20', 'max': '200', 'placeholder': 'Ej: 70.5'}
            ),
            'estatura_cm': forms.NumberInput(
                attrs={'class': 'form-control input-decimal-salud', 'step': '0.1',
                       'min': '100', 'max': '230', 'placeholder': 'Ej: 170'}
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
                       'placeholder': 'Notas adicionales sobre tu salud...',
                       'maxlength': '500'}
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
            if peso < 20 or peso > 200:
                raise ValidationError("El peso debe estar entre 20 y 200 kg.")
        return peso

    def clean_estatura_cm(self):
        estatura = self.cleaned_data.get('estatura_cm')
        if estatura is not None:
            if estatura <= 0:
                raise ValidationError("La estatura debe ser mayor a 0 cm. No se permiten valores de 0 o negativos.")
            if estatura < 100 or estatura > 230:
                raise ValidationError("La estatura debe estar entre 100 y 230 cm (ej: 170 para 1.70m).")
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

    def clean_observaciones(self):
        return limpiar_texto_largo(
            self.cleaned_data.get('observaciones', ''), 500, 'Las observaciones'
        )


class MaterialApoyoForm(forms.ModelForm):
    """Formulario para subir material de apoyo (admin/instructor)."""
    class Meta:
        model = MaterialApoyo
        fields = [
            'titulo', 'descripcion',
            'archivo', 'imagen_portada',
            'autor', 'fecha_publicacion', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'minlength': '2', 'maxlength': '150', 'placeholder': 'Ej: Guía Institucional de Nutrición SENA'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': '1000', 'placeholder': 'Descripción breve del material de apoyo...'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control d-none custom-file-input-hidden', 'accept': '.pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg'}),
            'imagen_portada': forms.ClearableFileInput(attrs={'class': 'form-control d-none custom-file-input-hidden', 'accept': 'image/*'}),
            'autor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'placeholder': 'Ej: Bienestar al Aprendiz SENA'}),
            'fecha_publicacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titulo': 'Título del Material',
            'descripcion': 'Descripción',
            'archivo': 'Documento o Archivo Adjunto (PDF, Word, Infografía)',
            'imagen_portada': 'Imagen de Portada (opcional)',
            'autor': 'Autor / Dependencia',
            'fecha_publicacion': 'Fecha de Publicación',
            'activo': 'Material Activo (visible en la biblioteca)',
        }

    def clean(self):
        cleaned = super().clean()
        archivo = cleaned.get('archivo')
        if archivo and hasattr(archivo, 'content_type'):
            try:
                validate_uploaded_file(archivo, allowed_types="document")
            except ValidationError:
                try:
                    validate_uploaded_file(archivo, allowed_types="image")
                except ValidationError:
                    self.add_error(
                        'archivo',
                        'Tipo de archivo no permitido o archivo inválido.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        archivo = self.cleaned_data.get('archivo')
        if archivo and hasattr(archivo, 'name'):
            ext = archivo.name.rsplit('.', 1)[-1].lower() if '.' in archivo.name else ''
            if ext == 'pdf':
                instance.tipo_contenido = 'pdf'
            elif ext in ('ppt', 'pptx'):
                instance.tipo_contenido = 'presentacion'
            elif ext in ('png', 'jpg', 'jpeg', 'webp'):
                instance.tipo_contenido = 'infografia'
            else:
                instance.tipo_contenido = 'documento'
        elif not instance.tipo_contenido:
            instance.tipo_contenido = 'documento'
        if commit:
            instance.save()
        return instance

    def clean_titulo(self):
        return limpiar_texto_largo(self.cleaned_data.get('titulo', ''), 250, 'El título')

    def clean_descripcion(self):
        return limpiar_texto_largo(self.cleaned_data.get('descripcion', ''), 1000, 'La descripción')

    def clean_autor(self):
        return limpiar_texto_largo(self.cleaned_data.get('autor', ''), 150, 'El autor')


class RecetaSaludableForm(forms.ModelForm):
    tiempo_preparacion_min = forms.IntegerField(min_value=1, max_value=1440)
    porciones = forms.IntegerField(min_value=1, max_value=100)
    calorias_por_porcion = forms.IntegerField(min_value=0, max_value=10000, required=False)
    proteinas_g = forms.DecimalField(min_value=0, max_value=500, required=False, max_digits=5, decimal_places=1)
    carbohidratos_g = forms.DecimalField(min_value=0, max_value=1000, required=False, max_digits=5, decimal_places=1)
    grasas_g = forms.DecimalField(min_value=0, max_value=500, required=False, max_digits=5, decimal_places=1)

    class Meta:
        model = RecetaSaludable
        fields = [
            'titulo', 'descripcion', 'ingredientes', 'preparacion',
            'tiempo_preparacion_min', 'porciones', 'calorias_por_porcion',
            'proteinas_g', 'carbohidratos_g', 'grasas_g', 'categoria',
            'objetivo', 'imagen',
        ]

    def clean_titulo(self):
        return limpiar_texto_largo(self.cleaned_data.get('titulo', ''), 250, 'El título')

    def clean_descripcion(self):
        return limpiar_texto_largo(self.cleaned_data.get('descripcion', ''), 500, 'La descripción')

    def clean_ingredientes(self):
        return limpiar_texto_largo(self.cleaned_data.get('ingredientes', ''), 2000, 'Los ingredientes')

    def clean_preparacion(self):
        return limpiar_texto_largo(self.cleaned_data.get('preparacion', ''), 3000, 'La preparación')

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            validate_uploaded_file(imagen, allowed_types='image')
        return imagen


class HabitoSaludableForm(forms.ModelForm):
    """Formulario para crear y editar Hábitos Saludables en la interfaz web."""
    class Meta:
        model = HabitoSaludable
        fields = ['titulo', 'categoria', 'descripcion', 'consejos', 'imagen', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Hidratación Óptima', 'maxlength': '200'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del hábito saludable...'}),
            'consejos': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe un consejo por línea...'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titulo': 'Título del Hábito',
            'categoria': 'Categoría',
            'descripcion': 'Descripción',
            'consejos': 'Consejos Clave (uno por línea)',
            'imagen': 'Imagen Ilustrativa',
            'activo': 'Hábito Activo (visible para aprendices)',
        }


class RutinaFisicaForm(forms.ModelForm):
    """Formulario para crear y editar Rutinas Físicas en la interfaz web."""
    class Meta:
        model = RutinaFisica
        fields = ['nombre', 'nivel', 'objetivo', 'duracion_minutos', 'descripcion', 'ejercicios', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cardio Express 20 Min', 'maxlength': '200'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'objetivo': forms.Select(attrs={'class': 'form-select'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '360', 'placeholder': 'Ej: 30'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la rutina...'}),
            'ejercicios': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe un ejercicio por línea (ej: Sentadillas 3x15)...'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Rutina',
            'nivel': 'Nivel de Dificultad',
            'objetivo': 'Objetivo Principal',
            'duracion_minutos': 'Duración Estimada (minutos)',
            'descripcion': 'Descripción',
            'ejercicios': 'Lista de Ejercicios (uno por línea)',
            'imagen': 'Imagen de la Rutina',
            'activo': 'Rutina Activa (visible para aprendices)',
        }


class PiramideNutricionalForm(forms.ModelForm):
    """Formulario para crear y editar elementos de la Pirámide Nutricional en la interfaz web."""
    class Meta:
        model = PiramideNutricional
        fields = ['nombre', 'categoria', 'nivel_piramide', 'cantidad_recomendada', 'beneficios', 'ejemplos', 'color_tarjeta', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Frutas y Vegetales', 'maxlength': '150'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nivel_piramide': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_recomendada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 3 a 5 porciones diarias'}),
            'beneficios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Beneficios nutricionales...'}),
            'ejemplos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Separados por coma: Manzana, Brócoli, Zanahoria'}),
            'color_tarjeta': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del Grupo / Alimento',
            'categoria': 'Categoría Nutricional',
            'nivel_piramide': 'Nivel en la Pirámide',
            'cantidad_recomendada': 'Porción / Cantidad Recomendada',
            'beneficios': 'Beneficios para la Salud',
            'ejemplos': 'Ejemplos de Alimentos (separados por comas)',
            'color_tarjeta': 'Color Distintivo',
            'imagen': 'Imagen Representativa',
            'activo': 'Elemento Activo',
        }


class BuscarMaterialForm(forms.Form):
    """Formulario de búsqueda/filtro para la biblioteca."""
    q = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar material...',
            'maxlength': '100'
        })
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + MaterialApoyo.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_q(self):
        return limpiar_texto_largo(self.cleaned_data.get('q', ''), 100, 'La búsqueda')
