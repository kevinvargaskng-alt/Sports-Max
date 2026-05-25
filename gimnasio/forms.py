# gimnasio/forms.py
# ══════════════════════════════════════════════════════════════
#  FORMULARIOS — Anamnesis, TestFisico, Rutina, EjercicioRutina
# ══════════════════════════════════════════════════════════════

from django import forms
from .models import Anamnesis, TestFisico, Rutina, EjercicioRutina


# ── Widgets compartidos ──────────────────────────────────────
class DarkInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('class', 'adm-input')

class DarkSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('class', 'adm-input')

class DarkTextarea(forms.Textarea):
    def __init__(self, rows=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('class', 'adm-input')
        self.attrs.setdefault('rows', rows)

class DarkNumberInput(forms.NumberInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('class', 'adm-input')

class DarkDateInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('class', 'adm-input')
        kwargs['attrs']['type'] = 'date'
        super().__init__(*args, **kwargs)


# ─────────────────────────────────────────────
#  ANAMNESIS
# ─────────────────────────────────────────────
class AnamnesisForm(forms.ModelForm):
    class Meta:
        model  = Anamnesis
        exclude = ['usuario', 'imc', 'clasificacion_imc', 'fecha_registro', 'actualizado_en']
        widgets = {
            'sexo':            DarkSelect(),
            'fecha_nacimiento': DarkDateInput(),
            'peso_kg':         DarkNumberInput(attrs={'step': '0.1', 'min': '20', 'max': '300'}),
            'talla_m':         DarkNumberInput(attrs={'step': '0.01', 'min': '1.00', 'max': '2.50',
                                                      'placeholder': 'ej: 1.75'}),
            'nivel_actividad': DarkSelect(),
            'horas_sueno':     DarkNumberInput(attrs={'min': '1', 'max': '24'}),
            'enfermedades':    DarkTextarea(rows=3),
            'medicamentos':    DarkTextarea(rows=2),
            'cirugias':        DarkTextarea(rows=2),
            'lesiones_previas': DarkTextarea(rows=2),
            'objetivo':        DarkTextarea(rows=3),
        }
        labels = {
            'sexo':            'Sexo biológico',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'peso_kg':         'Peso (kg)',
            'talla_m':         'Estatura (m)',
            'nivel_actividad': 'Nivel de actividad física',
            'fuma':            '¿Fuma actualmente?',
            'consume_alcohol': '¿Consume alcohol?',
            'horas_sueno':     'Horas de sueño por noche',
            'enfermedades':    'Enfermedades o condiciones médicas',
            'medicamentos':    'Medicamentos actuales',
            'cirugias':        'Cirugías previas',
            'lesiones_previas': 'Lesiones previas',
            'objetivo':        'Objetivo de entrenamiento',
        }


# ─────────────────────────────────────────────
#  TEST FÍSICO
# ─────────────────────────────────────────────
class TestFisicoForm(forms.ModelForm):
    class Meta:
        model  = TestFisico
        exclude = [
            'usuario', 'creado_en',
            'cooper_vo2max', 'cooper_categoria',
            'ruffier_indice', 'ruffier_clasificacion',
        ]
        widgets = {
            'tipo':               DarkSelect(),
            'fecha':              DarkDateInput(),
            'cooper_distancia_m': DarkNumberInput(attrs={'min': '0', 'max': '5000',
                                                          'placeholder': 'metros recorridos'}),
            'ruffier_p0':         DarkNumberInput(attrs={'min': '0', 'max': '250',
                                                          'placeholder': 'pulsaciones/min'}),
            'ruffier_p1':         DarkNumberInput(attrs={'min': '0', 'max': '250',
                                                          'placeholder': 'pulsaciones/min'}),
            'ruffier_p2':         DarkNumberInput(attrs={'min': '0', 'max': '250',
                                                          'placeholder': 'pulsaciones/min'}),
            'observaciones':      DarkTextarea(rows=3),
        }
        labels = {
            'tipo':               'Tipo de test',
            'fecha':              'Fecha del test',
            'cooper_distancia_m': 'Distancia recorrida (m) en 12 min',
            'ruffier_p0':         'P0 — Pulso en reposo (ppm)',
            'ruffier_p1':         'P1 — Pulso al terminar 45 sentadillas (ppm)',
            'ruffier_p2':         'P2 — Pulso al minuto de recuperación (ppm)',
            'observaciones':      'Observaciones',
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        if tipo == 'cooper' and not cleaned.get('cooper_distancia_m'):
            self.add_error('cooper_distancia_m',
                           'Ingresa la distancia recorrida para el Test de Cooper.')
        if tipo == 'ruffier_dickson':
            for f in ['ruffier_p0', 'ruffier_p1', 'ruffier_p2']:
                if not cleaned.get(f):
                    self.add_error(f, 'Este campo es requerido para Ruffier-Dickson.')
        return cleaned


# ─────────────────────────────────────────────
#  RUTINA
# ─────────────────────────────────────────────
class RutinaForm(forms.ModelForm):
    class Meta:
        model  = Rutina
        fields = ['nombre', 'tipo', 'nivel', 'duracion_min', 'descripcion']
        widgets = {
            'nombre':       DarkInput(attrs={'placeholder': 'Ej: Cardio mañana — semana 1'}),
            'tipo':         DarkSelect(),
            'nivel':        DarkSelect(),
            'duracion_min': DarkNumberInput(attrs={'min': '10', 'max': '300'}),
            'descripcion':  DarkTextarea(rows=3),
        }
        labels = {
            'nombre':       'Nombre de la rutina',
            'tipo':         'Tipo de entrenamiento',
            'nivel':        'Nivel',
            'duracion_min': 'Duración total (minutos)',
            'descripcion':  'Descripción / notas',
        }


# ─────────────────────────────────────────────
#  EJERCICIO DENTRO DE RUTINA
# ─────────────────────────────────────────────
class EjercicioRutinaForm(forms.ModelForm):
    class Meta:
        model  = EjercicioRutina
        exclude = ['rutina']
        widgets = {
            'orden':         DarkNumberInput(attrs={'min': '1', 'max': '50'}),
            'nombre':        DarkInput(attrs={'placeholder': 'Ej: Press de pecho'}),
            'maquina':       DarkSelect(),
            'series':        DarkNumberInput(attrs={'min': '1', 'max': '20'}),
            'repeticiones':  DarkNumberInput(attrs={'min': '1', 'max': '100'}),
            'duracion_min':  DarkNumberInput(attrs={'min': '1', 'max': '120'}),
            'peso_kg':       DarkNumberInput(attrs={'step': '0.5', 'min': '0', 'max': '500'}),
            'descanso_seg':  DarkNumberInput(attrs={'min': '0', 'max': '600'}),
            'notas':         DarkTextarea(rows=2),
        }
        labels = {
            'orden':        '# Orden',
            'nombre':       'Nombre del ejercicio',
            'maquina':      'Máquina / equipo',
            'series':       'Series',
            'repeticiones': 'Repeticiones',
            'duracion_min': 'Duración (min) — cardio',
            'peso_kg':      'Peso (kg)',
            'descanso_seg': 'Descanso entre series (seg)',
            'notas':        'Notas',
        }


# ── InlineFormSet para ejercicios dentro de una rutina ──────
EjercicioFormSet = forms.inlineformset_factory(
    Rutina, EjercicioRutina,
    form=EjercicioRutinaForm,
    extra=3,
    can_delete=True,
)