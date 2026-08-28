import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Usuario(AbstractUser):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    TIPO_DOC = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]
    GENERO_CHOICES = [
        ('M', 'Masculino'), ('F', 'Femenino'), ('O',
                                                'Otro'), ('NR', 'Prefiero no decirlo'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'), ('inactivo', 'Inactivo'),
        ('retiro_voluntario', 'Retiro Voluntario'), ('cancelado', 'Cancelado'),
    ]
    PROGRAMA_CHOICES = [
        ('ADSO', 'Análisis y Desarrollo de Software (ADSO)'),
        ('MINERIA', 'Supervisión de Procesos Mineros'),
        ('SST', 'Gestión de la Seguridad y Salud en el Trabajo'),
        ('QUIMICA', 'Química Aplicada a la Industria'),
        ('TOPOGRAFIA', 'Levantamientos Topográficos y Georreferenciación'),
        ('VIAL', 'Construcción de Infraestructura Vial'),
        ('SANEAMIENTO', 'Sistemas de Agua y Saneamiento'),
        ('MAQUINARIA_PESADA', 'Operación de Maquinaria Pesada para Excavación'),
        ('MANTENIMIENTO_EQUIPO', 'Mantenimiento de Equipo Pesado'),
    ]

    numero_documento = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    tipo_documento = models.CharField(
        max_length=2, choices=TIPO_DOC, default='CC')
    telefono = models.CharField(max_length=15, blank=True)
    genero = models.CharField(
        max_length=2, choices=GENERO_CHOICES, blank=True, null=True)
    ficha = models.CharField(max_length=20, blank=True, null=True)
    programa_formacion = models.CharField(
        max_length=25, choices=PROGRAMA_CHOICES, blank=True, null=True)
    rol = models.CharField(max_length=20, default='aprendiz')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='activo')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    foto_perfil = models.ImageField(
        upload_to='perfiles/', blank=True, null=True)
    foto_posicion = models.CharField(max_length=50, default='50% 50%')
    # ── Seguridad: bloqueo por intentos fallidos ──────────────
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.numero_documento})"

    @property
    def iniciales(self):
        first = self.first_name.strip() if self.first_name else ""
        last = self.last_name.strip() if self.last_name else ""
        ini = ""
        if first:
            ini += first[0].upper()
        if last:
            ini += last[0].upper()
        if not ini:
            if self.username:
                ini = self.username[:2].upper()
            else:
                ini = "US"
        return ini


class Sugerencia(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=50, default='otro')
    comentario = models.TextField()
    anonimo = models.BooleanField(default=False)
    respuesta = models.TextField(null=True, blank=True)
    imagen = models.ImageField(
        upload_to='reportes_errores/', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sugerencia #{self.pk} - {self.tipo}"


# ═══════════════════════════════════════════════════════════
#  CP-02: HISTORIAL DE ACCIONES (AUDITORÍA EN BASE DE DATOS)
# ═══════════════════════════════════════════════════════════
class HistorialAccion(models.Model):
    """
    Tabla de historial_acciones para registrar qué usuario modificó qué dato,
    en qué módulo y en qué fecha/hora.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial_acciones',
        verbose_name="Usuario que realizó la acción"
    )
    modulo = models.CharField(max_length=50, verbose_name="Módulo")
    accion = models.CharField(max_length=100, verbose_name="Acción Realizada")
    descripcion = models.TextField(verbose_name="Detalles de la Modificación")
    ip_origen = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP de Origen")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        db_table = 'historial_acciones'
        verbose_name = 'Historial de Acción'
        verbose_name_plural = 'Historial de Acciones'
        ordering = ['-fecha']

    def __str__(self):
        usr = self.usuario.username if self.usuario else "Anónimo/Sistema"
        return f"[{self.fecha.strftime('%d/%m/%Y %H:%M')}] {usr} -> {self.accion} ({self.modulo})"

