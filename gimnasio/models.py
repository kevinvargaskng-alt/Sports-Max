from django.db import models
from usuarios.models import Usuario
from django.conf import settings




class Reserva(models.Model):
    codigo_registro = models.AutoField(primary_key=True)
    # CAMBIO: De CharField a ForeignKey (Punto 6 del MER)
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservas_gimnasio'
    )
    fecha_entrada = models.DateField()
    hora_entrada = models.TimeField()
    # CAMBIO: Renombrar para coincidir con el MER
    tiempo_permanencia = models.IntegerField(
        help_text="Tiempo en minutos", default=60)
    hora_salida = models.TimeField()
    fecha_salida = models.DateField()
    estado = models.CharField(max_length=20, default='Pendiente')

    def __str__(self):
        return f"{self.usuario_solicitante.get_full_name()} - {self.fecha_entrada}"


class GimnasioConfig(models.Model):
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


class Maquina(models.Model):
    CATEGORIAS = [
        ('cardio', 'Cardio'),
        ('fuerza', 'Fuerza'),
        ('funcional', 'Funcional'),
    ]
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('mantenimiento', 'Mantenimiento'),
        ('inactivo', 'Fuera de Servicio'),
    ]
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='fuerza')
    descripcion = models.TextField(blank=True)
    musculos = models.JSONField(default=list, blank=True)
    imagen = models.ImageField(upload_to='maquinas/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')

    class Meta:
        ordering = ['categoria', 'nombre']
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'

    def __str__(self):
        return self.nombre

    @property
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url
        # Mapea nombres de máquinas por defecto a sus respectivas imágenes estáticas
        mapping = {
            'caminadora': 'caminadora.jpg',
            'bicicleta estática': 'bicicleta.jpg',
            'elíptica': 'eliptica.jpg',
            'press de banca': 'press_banca.jpg',
            'multiestación': 'multifuerza.jpg',
            'rack de sentadillas': 'rack_sentadillas.jpg',
            'remo': 'remo.jpg',
            'zona trx / colchonetas': 'trx_colchonetas.jpg'
        }
        filename = mapping.get(self.nombre.lower(), 'mancuernas.jpg')
        return f"/static/img/maquinas/{filename}"


class Machine(models.Model):
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
        verbose_name = 'Máquina (Machine)'
        verbose_name_plural = 'Máquinas (Machines)'

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    @property
    def badge_icon(self):
        """Devuelve la clase de FontAwesome correspondiente al tipo de máquina."""
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