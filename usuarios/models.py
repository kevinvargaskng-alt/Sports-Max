from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 

class Usuario(AbstractUser):
    TIPO_DOC = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]
    GENERO_CHOICES = [
        ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro'), ('NR', 'Prefiero no decirlo'),
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
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOC, default='CC')
    telefono = models.CharField(max_length=15, blank=True)
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES, blank=True, null=True)
    ficha = models.CharField(max_length=20, blank=True, null=True)
    programa_formacion = models.CharField(max_length=25, choices=PROGRAMA_CHOICES, blank=True, null=True)
    rol = models.CharField(max_length=20, default='aprendiz')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)

    # --- CAMBIO 1: Configuración para createsuperuser ---
    # Esto obliga a la terminal a pedirte estos datos adicionales.
    # El 'username' y 'password' no se ponen aquí porque Django los pide siempre.
    REQUIRED_FIELDS = ['email', 'numero_documento', 'tipo_documento']

    def __str__(self):
        # --- CAMBIO 2: Mejora de representación ---
        # Si el usuario no tiene nombre/apellido aún, mostrar el username para evitar strings vacíos.
        identificador = self.get_full_name() if self.get_full_name().strip() else self.username
        return f"{identificador} ({self.numero_documento})"
    
class Sugerencia(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=50, default='otro')
    comentario = models.TextField()
    anonimo = models.BooleanField(default=False) 
    respuesta = models.TextField(null=True, blank=True)
    imagen = models.ImageField(upload_to='reportes_errores/', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sugerencia #{self.pk} - {self.tipo}"