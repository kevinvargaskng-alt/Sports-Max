import uuid
from django.db import models
from usuarios.models import Usuario
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from core.validators import validador_nombre_con_numeros




class Reserva(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

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
        help_text="Tiempo en minutos", default=60,
        validators=[MinValueValidator(1, message='La permanencia debe ser al menos 1 minuto.'),
                    MaxValueValidator(1440, message='La permanencia no puede superar 1440 minutos.')])
    hora_salida = models.TimeField()
    fecha_salida = models.DateField()
    franja_horaria = models.ForeignKey(
        'FranjaHoraria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservas'
    )
    estado = models.CharField(max_length=20, default='Pendiente')

    def clean(self):
        if self.fecha_entrada and self.fecha_salida and self.fecha_salida < self.fecha_entrada:
            raise ValidationError({'fecha_salida': 'La fecha de salida no puede ser anterior a la fecha de entrada.'})
        super().clean()

    def __str__(self):
        return f"{self.usuario_solicitante.get_full_name()} - {self.fecha_entrada}"


class FranjaHoraria(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    dia_semana = models.CharField(max_length=20, default='Lunes')
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    aforo_maximo = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1, message='El aforo debe ser al menos 1.'),
                    MaxValueValidator(500, message='El aforo no puede superar 500 personas.')])
    habilitada = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        verbose_name = 'Franja Horaria'
        verbose_name_plural = 'Franjas Horarias'

    def __str__(self):
        return f"{self.dia_semana} {self.hora_inicio} - {self.hora_fin} (Aforo: {self.aforo_maximo})"


class GimnasioConfig(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    ESTADO_CHOICES = [
        ('abierta', 'Sala Abierta'),
        ('cerrada', 'Sala Cerrada'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='abierta')
    apertura_manual = models.BooleanField(
        default=False,
        help_text='Mantiene la sala abierta fuera del horario normal hasta que se cierre manualmente.'
    )
    dias_habilitados = models.JSONField(default=list)
    horario_apertura = models.TimeField(default='07:00')
    horario_cierre = models.TimeField(default='17:00')
    capacidad_maxima = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1, message='La capacidad debe ser al menos 1.'),
                    MaxValueValidator(500, message='La capacidad no puede superar 500 personas.')])
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


def _resolver_imagen_maquina(imagen_field, nombre, categoria=''):
    """Resuelve la URL válida de imagen de una máquina con respaldo estático garantizado."""
    if imagen_field and getattr(imagen_field, 'name', ''):
        try:
            if imagen_field.storage.exists(imagen_field.name):
                return imagen_field.url
        except Exception:
            pass

    nombre_norm = (nombre or '').lower()
    reglas_keywords = [
        (('bicicleta', 'spinning', 'ciclo', 'estática', 'estatica'), 'bicicleta.jpg'),
        (('caminadora', 'trotadora', 'banda caminadora', 'correr'), 'caminadora.jpg'),
        (('elíptica', 'eliptica', 'escaladora'), 'eliptica.jpg'),
        (('press', 'banca', 'pecho'), 'press_banca.jpg'),
        (('sentadilla', 'prensa', 'pierna', 'rack', 'smith', 'hack'), 'rack_sentadillas.jpg'),
        (('remo', 'espalda', 'dorsal', 'jalón', 'jalon'), 'remo.jpg'),
        (('trx', 'colchoneta', 'funcional', 'abdom', 'kettlebell', ' Rusa', 'flexibilidad', 'estiramiento', 'yoga'), 'trx_colchonetas.jpg'),
        (('multi', 'polea', 'fuerza', 'mancuerna', 'pesa', 'barra'), 'multifuerza.jpg'),
    ]
    for keywords, filename in reglas_keywords:
        if any(kw in nombre_norm for kw in keywords):
            return f"/static/img/maquinas/{filename}"

    cat_norm = (categoria or '').lower()
    if 'cardio' in cat_norm:
        return "/static/img/maquinas/caminadora.jpg"
    if 'funcional' in cat_norm or 'flexibilidad' in cat_norm:
        return "/static/img/maquinas/trx_colchonetas.jpg"
    return "/static/img/maquinas/multifuerza.jpg"


class Maquina(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

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
    # REVISAR: los nombres de máquinas suelen incluir modelos (p. ej., Bicicleta 2).
    nombre = models.CharField(max_length=100, validators=[validador_nombre_con_numeros])
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
        return _resolver_imagen_maquina(self.imagen, self.nombre, self.categoria)


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

    # REVISAR: los nombres de máquinas suelen incluir modelos (p. ej., Bicicleta 2).
    nombre = models.CharField(max_length=100, validators=[validador_nombre_con_numeros], verbose_name="Nombre de la Máquina")
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
        return _resolver_imagen_maquina(self.imagen, self.nombre, self.tipo)
