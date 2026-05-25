from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

# ─────────────────────────────────────────────
#  1. CONFIGURACIÓN GENERAL DEL GIMNASIO
# ─────────────────────────────────────────────
class ConfiguracionGimnasio(models.Model):
    ESTADO_CHOICES = [
        ('abierta',       'Sala Abierta'),
        ('cerrada',       'Sala Cerrada'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    estado           = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierta')
    horario_apertura = models.TimeField(default='07:00')
    horario_cierre   = models.TimeField(default='17:00')
    capacidad_maxima = models.PositiveIntegerField(default=40)
    dias_habilitados = models.JSONField(default=list)   # ['lun','mar','mie','jue','vie']
    actualizado_en   = models.DateTimeField(auto_now=True)
    actualizado_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        verbose_name = 'Configuración del Gimnasio'

    def __str__(self):
        return f'Config Gimnasio — {self.get_estado_display()}'


# ─────────────────────────────────────────────
#  2. FECHAS ESPECIALES
# ─────────────────────────────────────────────
class FechaEspecial(models.Model):
    fecha       = models.DateField(unique=True)
    descripcion = models.CharField(max_length=200, blank=True)
    habilitada  = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Fecha Especial'

    def __str__(self):
        return f'{self.fecha} — {"✓" if self.habilitada else "✗"}'


# ─────────────────────────────────────────────
#  3. RESERVAS (MODELO FALTANTE)
# ─────────────────────────────────────────────
class Reserva(models.Model):
    ESTADO_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('asistio', 'Asistió'),
    ]

    codigo_reserva = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='reservas_gimnasio'
    )
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=15, choices=ESTADO_RESERVA, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-hora']
        verbose_name = 'Reserva'
        # Evita que un usuario reserve dos veces la misma hora el mismo día
        unique_together = ('usuario', 'fecha', 'hora')

    def __str__(self):
        return f'Reserva: {self.usuario} - {self.fecha} {self.hora}'


# ─────────────────────────────────────────────
#  4. REGISTRO DE INGRESO
# ─────────────────────────────────────────────
class RegistroIngreso(models.Model):
    codigo_registro = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ingresos_gimnasio'
    )
    fecha_entrada   = models.DateField()
    hora_entrada    = models.TimeField()
    creado_en       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_entrada', '-hora_entrada']
        verbose_name = 'Registro de Ingreso'

    def __str__(self):
        return f'{self.usuario} — {self.fecha_entrada} {self.hora_entrada}'


# ─────────────────────────────────────────────
#  5. ANAMNESIS / HISTORIA CLÍNICA DEPORTIVA
# ─────────────────────────────────────────────
class Anamnesis(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    NIVEL_CHOICES = [
        ('sedentario',   'Sedentario'),
        ('bajo',         'Bajo (1-2 días/semana)'),
        ('moderado',     'Moderado (3-4 días/semana)'),
        ('alto',         'Alto (5+ días/semana)'),
    ]
    
    IMC_LABELS = {
        'desnutricion':  'Desnutrición',
        'bajo_peso':     'Bajo peso',
        'normal':        'Normal',
        'sobrepeso':     'Sobrepeso',
        'obesidad_1':    'Obesidad Grado I',
        'obesidad_2':    'Obesidad Grado II',
        'obesidad_3':    'Obesidad Grado III',
    }

    usuario        = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='anamnesis'
    )
    fecha_registro = models.DateField(auto_now_add=True)
    sexo           = models.CharField(max_length=1, choices=SEXO_CHOICES)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    peso_kg        = models.DecimalField(max_digits=5, decimal_places=2, help_text='kg')
    talla_m        = models.DecimalField(max_digits=4, decimal_places=2, help_text='metros (ej: 1.75)')
    nivel_actividad = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='sedentario')

    fuma           = models.BooleanField(default=False)
    consume_alcohol = models.BooleanField(default=False)
    horas_sueno    = models.PositiveSmallIntegerField(default=8, help_text='horas por noche')
    enfermedades   = models.TextField(blank=True, help_text='Enfermedades o condiciones relevantes')
    medicamentos   = models.TextField(blank=True)
    cirugias       = models.TextField(blank=True)
    lesiones_previas = models.TextField(blank=True)
    objetivo       = models.TextField(blank=True, help_text='Objetivo de entrenamiento')

    imc            = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    clasificacion_imc = models.CharField(max_length=20, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Anamnesis'
        verbose_name_plural = 'Anamnesis'

    def calcular_imc(self):
        if self.peso_kg and self.talla_m and self.talla_m > 0:
            imc = float(self.peso_kg) / (float(self.talla_m) ** 2)
            self.imc = round(imc, 2)
            if imc < 16: self.clasificacion_imc = 'desnutricion'
            elif imc < 18.5: self.clasificacion_imc = 'bajo_peso'
            elif imc < 25: self.clasificacion_imc = 'normal'
            elif imc < 30: self.clasificacion_imc = 'sobrepeso'
            elif imc < 35: self.clasificacion_imc = 'obesidad_1'
            elif imc < 40: self.clasificacion_imc = 'obesidad_2'
            else: self.clasificacion_imc = 'obesidad_3'

    def save(self, *args, **kwargs):
        self.calcular_imc()
        super().save(*args, **kwargs)

    def get_clasificacion_display(self):
        return self.IMC_LABELS.get(self.clasificacion_imc, '—')

    def __str__(self):
        return f'Anamnesis de {self.usuario} — IMC {self.imc}'


# ─────────────────────────────────────────────
#  6. TESTS FÍSICOS
# ─────────────────────────────────────────────
class TestFisico(models.Model):
    TIPO_CHOICES = [
        ('cooper',          'Test de Cooper (resistencia)'),
        ('layer',           'Test de Layer (resistencia)'),
        ('ruffier_dickson', 'Test de Ruffier-Dickson (recuperación cardíaca)'),
    ]

    usuario       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tests_fisicos'
    )
    tipo          = models.CharField(max_length=30, choices=TIPO_CHOICES)
    fecha         = models.DateField(default=timezone.localdate)

    cooper_distancia_m = models.PositiveIntegerField(null=True, blank=True)
    cooper_vo2max      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cooper_categoria   = models.CharField(max_length=30, blank=True)

    ruffier_p0 = models.PositiveSmallIntegerField(null=True, blank=True)
    ruffier_p1 = models.PositiveSmallIntegerField(null=True, blank=True)
    ruffier_p2 = models.PositiveSmallIntegerField(null=True, blank=True)
    ruffier_indice = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ruffier_clasificacion = models.CharField(max_length=30, blank=True)

    observaciones = models.TextField(blank=True)
    creado_en     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Test Físico'

    def calcular_resultados(self):
        if self.tipo == 'cooper' and self.cooper_distancia_m:
            dist = self.cooper_distancia_m
            vo2 = (dist - 504.9) / 44.73
            self.cooper_vo2max = round(max(vo2, 0), 2)
            if vo2 >= 51: self.cooper_categoria = 'Excelente'
            elif vo2 >= 45: self.cooper_categoria = 'Muy Bueno'
            elif vo2 >= 38: self.cooper_categoria = 'Bueno'
            elif vo2 >= 35: self.cooper_categoria = 'Regular'
            else: self.cooper_categoria = 'Deficiente'

        if self.tipo == 'ruffier_dickson' and all([self.ruffier_p0, self.ruffier_p1, self.ruffier_p2]):
            indice = ((self.ruffier_p1 - 70) + 2 * (self.ruffier_p2 - self.ruffier_p0)) / 10
            self.ruffier_indice = round(indice, 2)
            if indice <= 0:   self.ruffier_clasificacion = 'Excelente'
            elif indice <= 5: self.ruffier_clasificacion = 'Bueno'
            elif indice <= 10: self.ruffier_clasificacion = 'Admisible'
            else:              self.ruffier_clasificacion = 'Insuficiente'

    def save(self, *args, **kwargs):
        self.calcular_resultados()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.usuario} ({self.fecha})'


# ─────────────────────────────────────────────
#  7. RUTINAS DE ENTRENAMIENTO
# ─────────────────────────────────────────────
class Rutina(models.Model):
    TIPO_CHOICES = [
        ('cardio',  'Cardio'),
        ('fuerza',  'Fuerza'),
        ('mixta',   'Mixta'),
    ]
    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio',   'Intermedio'),
        ('avanzado',     'Avanzado'),
    ]

    usuario       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='rutinas_gimnasio'
    )
    nombre         = models.CharField(max_length=100)
    tipo           = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nivel          = models.CharField(max_length=15, choices=NIVEL_CHOICES, default='principiante')
    duracion_min   = models.PositiveSmallIntegerField(default=60)
    descripcion    = models.TextField(blank=True)
    activa         = models.BooleanField(default=True)
    asignada_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='rutinas_asignadas'
    )
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Rutina'

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()}) — {self.usuario}'


class EjercicioRutina(models.Model):
    MAQUINA_CHOICES = [
        ('banda',          'Banda / Trotadora'),
        ('eliptica',       'Elíptica'),
        ('spinning',       'Spinning'),
        ('multifuncional', 'Multifuncional'),
        ('aductores',      'Máq. Aductores'),
        ('pecho',          'Máq. Pecho'),
        ('brazo',          'Máq. Brazo'),
        ('pierna',         'Máq. Pierna'),
        ('gluteo',         'Máq. Glúteo'),
        ('libre',          'Peso Libre'),
        ('otro',           'Otro'),
    ]

    rutina        = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='ejercicios')
    orden         = models.PositiveSmallIntegerField(default=1)
    nombre         = models.CharField(max_length=100)
    maquina       = models.CharField(max_length=20, choices=MAQUINA_CHOICES, default='otro')
    series        = models.PositiveSmallIntegerField(null=True, blank=True)
    repeticiones  = models.PositiveSmallIntegerField(null=True, blank=True)
    duracion_min  = models.PositiveSmallIntegerField(null=True, blank=True)
    peso_kg       = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    descanso_seg  = models.PositiveSmallIntegerField(default=60)
    notas         = models.TextField(blank=True)

    class Meta:
        ordering = ['orden']
        verbose_name = 'Ejercicio de Rutina'

    def __str__(self):
        return f'[{self.orden}] {self.nombre} — {self.rutina.nombre}'