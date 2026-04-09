from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    TIPO_DOC = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('NR', 'Prefiero no decirlo'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('retiro_voluntario', 'Retiro Voluntario'),
        ('cancelado', 'Cancelado'),
    ]

    PROGRAMA_CHOICES = [
        ('ADSO',                 'Análisis y Desarrollo de Software (ADSO)'),
        ('MINERIA',              'Supervisión de Procesos Mineros'),
        ('SST',                  'Gestión de la Seguridad y Salud en el Trabajo'),
        ('QUIMICA',              'Química Aplicada a la Industria'),
        ('TOPOGRAFIA',           'Levantamientos Topográficos y Georreferenciación'),
        ('VIAL',                 'Construcción de Infraestructura Vial'),
        ('SANEAMIENTO',          'Sistemas de Agua y Saneamiento'),
        ('MAQUINARIA_PESADA',    'Operación de Maquinaria Pesada para Excavación'),
        ('MANTENIMIENTO_EQUIPO', 'Mantenimiento de Equipo Pesado para Infraestructura, Minería y Transporte'),
    ]

    # Campos personalizados de identificación
    numero_documento = models.CharField(max_length=20, unique=True)
    
    # ✅ NUEVO: Hacemos que el correo sea único en toda la base de datos
    email            = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    
    tipo_documento   = models.CharField(max_length=2, choices=TIPO_DOC, default='CC')
    telefono         = models.CharField(max_length=15, blank=True)
    genero           = models.CharField(max_length=2, choices=GENERO_CHOICES, blank=True, null=True)
    
    # Campos académicos
    ficha            = models.CharField(max_length=20, blank=True, null=True)
    programa_formacion = models.CharField(max_length=25, choices=PROGRAMA_CHOICES, blank=True, null=True)
    
    rol              = models.CharField(max_length=20, default='aprendiz')
    estado           = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    fecha_registro   = models.DateTimeField(auto_now_add=True)
    foto_perfil      = models.ImageField(upload_to='perfiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.numero_documento})"