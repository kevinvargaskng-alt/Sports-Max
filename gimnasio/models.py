"""
models.py - Módulo Gimnasio Sports-Max SENA
CP-09: Consolidación de esquema (Machine → Maquina) + RutinaGimnasio
"""
import uuid
from django.db import models
from usuarios.models import Usuario
from django.conf import settings


# ─────────────────────────────────────────────────────────────
# RESERVAS DE GIMNASIO
# ─────────────────────────────────────────────────────────────
class Reserva(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    codigo_registro = models.AutoField(primary_key=True)
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservas_gimnasio'
    )
    fecha_entrada = models.DateField()
    hora_entrada = models.TimeField()
    tiempo_permanencia = models.IntegerField(
        help_text="Tiempo en minutos", default=60)
    hora_salida = models.TimeField()
    fecha_salida = models.DateField()
    estado = models.CharField(max_length=20, default='Pendiente', db_index=True)

    class Meta:
        verbose_name = 'Reserva de Gimnasio'
        verbose_name_plural = 'Reservas de Gimnasio'
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f"{self.usuario_solicitante.get_full_name()} - {self.fecha_entrada}"


# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL GIMNASIO
# ─────────────────────────────────────────────────────────────
class GimnasioConfig(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    ESTADO_CHOICES = [
        ('abierta', 'Sala Abierta'),
        ('cerrada', 'Sala Cerrada'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='abierta')
    dias_habilitados = models.JSONField(default=list)
    horario_apertura = models.TimeField(default='07:00')
    horario_cierre = models.TimeField(default='17:00')
    capacidad_maxima = models.PositiveIntegerField(default=40)
    actualizado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del Gimnasio'

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def __str__(self):
        return f"Config Gimnasio — {self.estado}"


# ─────────────────────────────────────────────────────────────
# FECHAS HABILITADAS (CALENDARIO)
# ─────────────────────────────────────────────────────────────
class FechaIngreso(models.Model):
    config = models.ForeignKey(
        GimnasioConfig, on_delete=models.CASCADE, related_name='fechas')
    fecha = models.DateField()
    descripcion = models.CharField(max_length=200, blank=True)
    habilitada = models.BooleanField(default=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Fecha de Ingreso'

    def __str__(self):
        return str(self.fecha)


# ─────────────────────────────────────────────────────────────
# MÁQUINAS DEL GIMNASIO
# CP-09: Consolidado con modelo Machine (eliminado el duplicado).
#        Se agregan: fecha_adquisicion, flexibilidad en categoria,
#        badge_icon, badge_color, estado_badge_color.
# ─────────────────────────────────────────────────────────────
class Maquina(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    CATEGORIAS = [
        ('cardio', 'Cardio'),
        ('fuerza', 'Fuerza'),
        ('funcional', 'Funcional'),
        ('flexibilidad', 'Flexibilidad / Salud'),
    ]
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('mantenimiento', 'En Mantenimiento'),
        ('inactivo', 'Fuera de Servicio'),
    ]
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Máquina')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIAS, default='fuerza', db_index=True,
        verbose_name='Categoría')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    musculos = models.JSONField(default=list, blank=True, verbose_name='Músculos trabajados')
    imagen = models.ImageField(upload_to='maquinas/', null=True, blank=True, verbose_name='Imagen')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='disponible', verbose_name='Estado')
    # CP-09: campo consolidado desde Machine
    fecha_adquisicion = models.DateField(
        null=True, blank=True, verbose_name='Fecha de Adquisición')

    class Meta:
        ordering = ['categoria', 'nombre']
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'

    def __str__(self):
        return self.nombre

    @property
    def badge_icon(self):
        """Devuelve la clase FontAwesome según la categoría."""
        icon_map = {
            'cardio': 'fa-heart',
            'fuerza': 'fa-dumbbell',
            'funcional': 'fa-bolt',
            'flexibilidad': 'fa-child',
        }
        return icon_map.get(self.categoria, 'fa-fire')

    @property
    def badge_color(self):
        color_map = {
            'cardio': 'danger',
            'fuerza': 'primary',
            'funcional': 'warning text-dark',
            'flexibilidad': 'info text-dark',
        }
        return color_map.get(self.categoria, 'secondary')

    @property
    def estado_badge_color(self):
        color_map = {
            'disponible': 'success',
            'mantenimiento': 'warning text-dark',
            'inactivo': 'danger',
        }
        return color_map.get(self.estado, 'secondary')

    @property
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url
        mapping = {
            'caminadora': 'caminadora.jpg',
            'bicicleta estática': 'bicicleta.jpg',
            'elíptica': 'eliptica.jpg',
            'press de banca': 'press_banca.jpg',
            'multiestación': 'multifuerza.jpg',
            'rack de sentadillas': 'rack_sentadillas.jpg',
            'remo': 'remo.jpg',
            'zona trx / colchonetas': 'trx_colchonetas.jpg',
        }
        filename = mapping.get(self.nombre.lower(), 'mancuernas.jpg')
        return f"/static/img/maquinas/{filename}"


# ─────────────────────────────────────────────────────────────
# CP-09: RUTINAS DEL GIMNASIO
# ─────────────────────────────────────────────────────────────
class RutinaGimnasio(models.Model):
    """
    Rutinas de entrenamiento creadas por entrenadores/admin.
    Se pueden asignar a usuarios aprendices.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    nombre = models.CharField(max_length=200, verbose_name='Nombre de la Rutina')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel = models.CharField(
        max_length=20, choices=NIVEL_CHOICES, default='principiante',
        verbose_name='Nivel')
    duracion_minutos = models.PositiveIntegerField(
        verbose_name='Duración (minutos)', default=60)
    maquinas = models.ManyToManyField(
        Maquina, blank=True, related_name='rutinas', verbose_name='Máquinas utilizadas')
    activo = models.BooleanField(default=True, verbose_name='Activa')
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rutinas_gimnasio_creadas',
        verbose_name='Creada por'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rutina de Gimnasio'
        verbose_name_plural = 'Rutinas de Gimnasio'
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_nivel_display()})"


# ─────────────────────────────────────────────────────────────
# COMPATIBILIDAD: Modelo Machine (tabla separada para panel admin)
# Nota: Las vistas usan Machine para el CRUD de inventario de máquinas.
# Se mantiene para no romper migraciones existentes.
# ─────────────────────────────────────────────────────────────
class Machine(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    TIPO_CHOICES = [
        ('Cardio', 'Cardio'),
        ('Fuerza', 'Fuerza'),
        ('Funcional', 'Funcional'),
        ('Flexibilidad', 'Flexibilidad / Salud'),
    ]
    ESTADO_CHOICES = [
        ('Disponible', 'Disponible'),
        ('En Mantenimiento', 'En Mantenimiento'),
        ('Fuera de Servicio', 'Fuera de Servicio'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Máquina")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='Cardio', verbose_name="Tipo")
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Disponible', verbose_name="Estado")
    imagen = models.ImageField(upload_to='maquinas/', null=True, blank=True, verbose_name="Imagen")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    fecha_adquisicion = models.DateField(null=True, blank=True, verbose_name="Fecha de Adquisición")

    class Meta:
        ordering = ['tipo', 'nombre']
        verbose_name = 'Máquina (Inventario)'
        verbose_name_plural = 'Máquinas (Inventario)'

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    @property
    def badge_icon(self):
        icon_map = {
            'Cardio': 'fa-heart',
            'Fuerza': 'fa-dumbbell',
            'Funcional': 'fa-bolt',
            'Flexibilidad': 'fa-child',
        }
        return icon_map.get(self.tipo, 'fa-fire')

    @property
    def badge_color(self):
        color_map = {
            'Cardio': 'danger',
            'Fuerza': 'primary',
            'Funcional': 'warning text-dark',
            'Flexibilidad': 'info text-dark',
        }
        return color_map.get(self.tipo, 'secondary')

    @property
    def estado_badge_color(self):
        color_map = {
            'Disponible': 'success',
            'En Mantenimiento': 'warning text-dark',
            'Fuera de Servicio': 'danger',
        }
        return color_map.get(self.estado, 'secondary')

    @property
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url
        mapping = {
            'caminadora': 'caminadora.jpg',
            'bicicleta estática': 'bicicleta.jpg',
            'elíptica': 'eliptica.jpg',
            'press de banca': 'press_banca.jpg',
            'multiestación': 'multifuerza.jpg',
            'rack de sentadillas': 'rack_sentadillas.jpg',
            'remo': 'remo.jpg',
        }
        filename = mapping.get(self.nombre.lower(), 'mancuernas.jpg')
        return f"/static/img/maquinas/{filename}"