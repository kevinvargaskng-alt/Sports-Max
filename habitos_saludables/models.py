"""
models.py - Módulo Hábitos Saludables SENA
"""

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ─────────────────────────────────────────────
# HABEAS DATA CONSENT
# ─────────────────────────────────────────────
class HabeasDataConsent(models.Model):
    """
    Registro de aceptación del tratamiento de datos personales.
    Obligatorio antes de registrar información médica.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habeas_data',
        verbose_name='Usuario'
    )

    fecha_aceptacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de aceptación'
    )

    direccion_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )

    acepta = models.BooleanField(
        default=False,
        verbose_name='Acepta tratamiento de datos'
    )

    version_politica = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='Versión de política'
    )

    class Meta:
        verbose_name = 'Consentimiento Habeas Data'
        verbose_name_plural = 'Consentimientos Habeas Data'

    def __str__(self):
        estado = '✓ Aceptado' if self.acepta else '✗ Rechazado'
        return f"{self.usuario.get_full_name()} — {estado}"


# ─────────────────────────────────────────────
# HÁBITOS SALUDABLES
# ─────────────────────────────────────────────
class HabitoSaludable(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    CATEGORIA_CHOICES = [
        ('ejercicio', 'Ejercicio Físico'),
        ('alimentacion', 'Alimentación Saludable'),
        ('mental', 'Salud Mental'),
        ('hidratacion', 'Hidratación'),
        ('sueno', 'Calidad del Sueño'),
        ('prevencion', 'Prevención de Enfermedades'),
    ]

    titulo = models.CharField(max_length=200)

    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES
    )

    descripcion = models.TextField()

    consejos = models.TextField(
        blank=True,
        help_text='Separar consejos por saltos de línea'
    )

    imagen = models.ImageField(
        upload_to='habitos/imagenes/',
        null=True,
        blank=True
    )

    icono_css = models.CharField(
        max_length=50,
        default='bi-heart-pulse'
    )

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hábito Saludable'
        verbose_name_plural = 'Hábitos Saludables'
        ordering = ['categoria', 'titulo']

    def __str__(self):
        return self.titulo

    def get_consejos_lista(self):
        if self.consejos:
            return [
                c.strip()
                for c in self.consejos.split('\n')
                if c.strip()
            ]
        return []


# ─────────────────────────────────────────────
# RUTINAS FÍSICAS
# ─────────────────────────────────────────────
class RutinaFisica(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    OBJETIVO_CHOICES = [
        ('fuerza', 'Fuerza'),
        ('cardio', 'Cardio'),
        ('flexibilidad', 'Flexibilidad'),
        ('perdida_peso', 'Pérdida de peso'),
        ('bienestar', 'Bienestar general'),
    ]

    nombre = models.CharField(max_length=200)

    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES
    )

    objetivo = models.CharField(
        max_length=30,
        choices=OBJETIVO_CHOICES
    )

    descripcion = models.TextField()

    duracion_minutos = models.PositiveIntegerField()

    ejercicios = models.TextField(
        help_text='Un ejercicio por línea'
    )

    imagen = models.ImageField(
        upload_to='rutinas/imagenes/',
        null=True,
        blank=True
    )

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rutina Física'
        verbose_name_plural = 'Rutinas Físicas'

    def __str__(self):
        return self.nombre

    def get_ejercicios_lista(self):
        return [
            e.strip()
            for e in self.ejercicios.split('\n')
            if e.strip()
        ]


# ─────────────────────────────────────────────
# PIRÁMIDE NUTRICIONAL
# ─────────────────────────────────────────────
class PiramideNutricional(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    CATEGORIA_CHOICES = [
        ('cereales', 'Cereales'),
        ('frutas', 'Frutas'),
        ('verduras', 'Verduras'),
        ('proteinas', 'Proteínas'),
        ('lacteos', 'Lácteos'),
        ('grasas', 'Grasas saludables'),
        ('azucares', 'Azúcares'),
        ('agua', 'Agua'),
    ]

    NIVEL_PIRAMIDE_CHOICES = [
        (1, 'Base'),
        (2, 'Segundo nivel'),
        (3, 'Tercer nivel'),
        (4, 'Cuarto nivel'),
        (5, 'Cúspide'),
    ]

    nombre = models.CharField(max_length=150)

    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES
    )

    nivel_piramide = models.IntegerField(
        choices=NIVEL_PIRAMIDE_CHOICES,
        default=1
    )

    beneficios = models.TextField()

    cantidad_recomendada = models.CharField(max_length=100)

    ejemplos = models.TextField(
        blank=True,
        help_text='Separar ejemplos con comas'
    )

    imagen = models.ImageField(
        upload_to='nutricion/imagenes/',
        null=True,
        blank=True
    )

    color_tarjeta = models.CharField(
        max_length=20,
        default='#4CAF50'
    )

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pirámide Nutricional'
        verbose_name_plural = 'Pirámide Nutricional'

    def __str__(self):
        return self.nombre

    def get_ejemplos_lista(self):
        if self.ejemplos:
            return [
                e.strip()
                for e in self.ejemplos.split(',')
                if e.strip()
            ]
        return []


# ─────────────────────────────────────────────
# MATERIAL DE APOYO
# ─────────────────────────────────────────────
class MaterialApoyo(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    TIPO_CHOICES = [
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('documento', 'Documento'),
        ('infografia', 'Infografía'),
        ('presentacion', 'Presentación'),
    ]

    titulo = models.CharField(max_length=250)

    descripcion = models.TextField()

    tipo_contenido = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )

    archivo = models.FileField(
        upload_to='materiales/archivos/',
        null=True,
        blank=True
    )

    url_video = models.URLField(
        null=True,
        blank=True
    )

    imagen_portada = models.ImageField(
        upload_to='materiales/portadas/',
        null=True,
        blank=True
    )

    autor = models.CharField(
        max_length=150,
        default='SENA'
    )

    fecha_publicacion = models.DateField(
        default=timezone.now
    )

    descargas = models.PositiveIntegerField(default=0)

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Material de Apoyo'
        verbose_name_plural = 'Materiales de Apoyo'

    def __str__(self):
        return self.titulo

    def incrementar_descargas(self):
        self.descargas += 1
        self.save(update_fields=['descargas'])


# ─────────────────────────────────────────────
# SEGUIMIENTO DE SALUD
# ─────────────────────────────────────────────
class SeguimientoSalud(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario'),
        ('ligero', 'Ligero'),
        ('moderado', 'Moderado'),
        ('activo', 'Activo'),
        ('muy_activo', 'Muy activo'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seguimientos'
    )

    fecha_evaluacion = models.DateField(
        default=timezone.now
    )

    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(20),
            MaxValueValidator(300)
        ]
    )

    estatura_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(100),
            MaxValueValidator(250)
        ]
    )

    imc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    presion_sistolica = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    presion_diastolica = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    frecuencia_cardiaca = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    nivel_actividad = models.CharField(
        max_length=20,
        choices=ACTIVIDAD_CHOICES,
        default='sedentario'
    )

    horas_sueno = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    vasos_agua = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    observaciones = models.TextField(
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Seguimiento de Salud'
        verbose_name_plural = 'Seguimientos de Salud'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.fecha_evaluacion}"

    def calcular_imc(self):
        if self.peso_kg and self.estatura_cm:
            estatura_m = float(self.estatura_cm) / 100
            return round(
                float(self.peso_kg) / (estatura_m ** 2),
                2
            )
        return None

    def get_categoria_imc(self):

        if not self.imc:
            return 'Sin calcular'

        imc = float(self.imc)

        if imc < 18.5:
            return 'Bajo peso'
        elif imc < 25:
            return 'Peso normal'
        elif imc < 30:
            return 'Sobrepeso'
        else:
            return 'Obesidad'

    def save(self, *args, **kwargs):
        self.imc = self.calcular_imc()
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# CP-09 / CP-13: RECETAS SALUDABLES
# ─────────────────────────────────────────────────────────────
class RecetaSaludable(models.Model):
    """
    Base de datos de recetas saludables administrada por nutricionistas.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    CATEGORIA_CHOICES = [
        ('desayuno', 'Desayuno'),
        ('almuerzo', 'Almuerzo'),
        ('cena', 'Cena'),
        ('snack', 'Snack / Merienda'),
        ('bebida', 'Bebida Saludable'),
    ]
    OBJETIVO_CHOICES = [
        ('perdida_peso', 'Pérdida de peso'),
        ('ganancia_muscular', 'Ganancia muscular'),
        ('mantenimiento', 'Mantenimiento'),
        ('vegana', 'Vegana / Vegetariana'),
        ('diabeticos', 'Para diabéticos'),
    ]

    titulo = models.CharField(max_length=250, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    ingredientes = models.TextField(
        verbose_name='Ingredientes',
        help_text='Un ingrediente por línea')
    preparacion = models.TextField(verbose_name='Pasos de preparación')
    tiempo_preparacion_min = models.PositiveIntegerField(
        default=30, verbose_name='Tiempo de preparación (min)')
    porciones = models.PositiveIntegerField(default=1, verbose_name='Porciones')
    calorias_por_porcion = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Calorías por porción')
    proteinas_g = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Proteínas (g)')
    carbohidratos_g = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Carbohidratos (g)')
    grasas_g = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Grasas (g)')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIA_CHOICES, default='almuerzo',
        verbose_name='Categoría', db_index=True)
    objetivo = models.CharField(
        max_length=25, choices=OBJETIVO_CHOICES, default='mantenimiento',
        verbose_name='Objetivo nutricional')
    imagen = models.ImageField(
        upload_to='recetas/', null=True, blank=True, verbose_name='Imagen')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recetas_creadas',
        verbose_name='Creada por'
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Receta Saludable'
        verbose_name_plural = 'Recetas Saludables'
        ordering = ['categoria', 'titulo']

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"

    def get_ingredientes_lista(self):
        return [i.strip() for i in self.ingredientes.split('\n') if i.strip()]

    def get_preparacion_lista(self):
        return [p.strip() for p in self.preparacion.split('\n') if p.strip()]


# ─────────────────────────────────────────────────────────────
# CP-09 / CP-11: REGISTRO DE HÁBITO POR USUARIO
# ─────────────────────────────────────────────────────────────
class RegistroHabitoUsuario(models.Model):
    """
    Registro diario de si el usuario completó un hábito saludable.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_habitos',
        verbose_name='Usuario'
    )
    habito = models.ForeignKey(
        HabitoSaludable,
        on_delete=models.CASCADE,
        related_name='registros',
        verbose_name='Hábito'
    )
    fecha = models.DateField(verbose_name='Fecha')
    completado = models.BooleanField(default=False, verbose_name='Completado')
    nota = models.TextField(blank=True, verbose_name='Nota personal')

    class Meta:
        verbose_name = 'Registro de Hábito'
        verbose_name_plural = 'Registros de Hábitos'
        unique_together = [('usuario', 'habito', 'fecha')]
        ordering = ['-fecha']

    def __str__(self):
        estado = '✓' if self.completado else '✗'
        return f"{self.usuario.get_full_name()} — {self.habito.titulo} {estado} ({self.fecha})"


# ─────────────────────────────────────────────────────────────
# CP-09 / CP-15: REGISTRO DE SUEÑO
# ─────────────────────────────────────────────────────────────
class RegistroSueno(models.Model):
    """
    Registro diario de horas de sueño del usuario.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    CALIDAD_CHOICES = [
        (1, '⭐ Muy malo'),
        (2, '⭐⭐ Malo'),
        (3, '⭐⭐⭐ Regular'),
        (4, '⭐⭐⭐⭐ Bueno'),
        (5, '⭐⭐⭐⭐⭐ Excelente'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_sueno',
        verbose_name='Usuario'
    )
    fecha = models.DateField(verbose_name='Fecha')
    horas = models.DecimalField(
        max_digits=4, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        verbose_name='Horas dormidas'
    )
    calidad = models.IntegerField(
        choices=CALIDAD_CHOICES, default=3,
        verbose_name='Calidad del sueño (1-5)'
    )
    nota = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Registro de Sueño'
        verbose_name_plural = 'Registros de Sueño'
        unique_together = [('usuario', 'fecha')]
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.get_full_name()} — {self.fecha}: {self.horas}h"

    @property
    def es_optimo(self):
        """Verifica si las horas están en el rango recomendado (7-9 h)."""
        return 7 <= float(self.horas) <= 9

    @property
    def categoria_texto(self):
        h = float(self.horas)
        if h >= 9:
            return 'Óptimo (máximo)'
        elif h >= 7:
            return 'Óptimo'
        elif h >= 5:
            return 'Insuficiente'
        return 'Muy poco'


# ─────────────────────────────────────────────────────────────
# CP-09 / CP-12: SUSCRIPCIÓN PUSH
# ─────────────────────────────────────────────────────────────
class SuscripcionPush(models.Model):
    """
    Almacena los endpoints de suscripción Web Push por usuario.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suscripciones_push',
        verbose_name='Usuario'
    )
    endpoint = models.URLField(max_length=1000, verbose_name='Endpoint Push')
    p256dh = models.CharField(max_length=500, verbose_name='Clave p256dh')
    auth = models.CharField(max_length=200, verbose_name='Clave auth')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción Push'
        verbose_name_plural = 'Suscripciones Push'

    def __str__(self):
        estado = 'activa' if self.activa else 'inactiva'
        return f"Push {estado} — {self.usuario.username}"


# ─────────────────────────────────────────────────────────────
# CP-09 / CP-11: REGISTRO DE SESIÓN DE RUTINA
# ─────────────────────────────────────────────────────────────
class RegistroSesionRutina(models.Model):
    """
    Registra cada sesión de entrenamiento completada por el usuario.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    ESFUERZO_CHOICES = [
        (1, '😴 Muy fácil'),
        (2, '🙂 Fácil'),
        (3, '😤 Moderado'),
        (4, '🥵 Difícil'),
        (5, '💪 Máximo esfuerzo'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sesiones_rutina',
        verbose_name='Usuario'
    )
    rutina = models.ForeignKey(
        RutinaFisica,
        on_delete=models.CASCADE,
        related_name='sesiones',
        verbose_name='Rutina'
    )
    fecha = models.DateField(verbose_name='Fecha de la sesión')
    duracion_real_min = models.PositiveIntegerField(
        verbose_name='Duración real (min)', default=0)
    completado = models.BooleanField(default=False, verbose_name='Completada')
    nivel_esfuerzo = models.IntegerField(
        choices=ESFUERZO_CHOICES, default=3,
        verbose_name='Nivel de esfuerzo (1-5)'
    )
    notas = models.TextField(blank=True, verbose_name='Notas')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sesión de Rutina'
        verbose_name_plural = 'Sesiones de Rutina'
        ordering = ['-fecha']

    def __str__(self):
        estado = '✓' if self.completado else '✗'
        return f"{self.usuario.get_full_name()} — {self.rutina.nombre} {estado} ({self.fecha})"
