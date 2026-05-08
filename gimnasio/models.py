from django.db import models
from usuarios.models import Usuario

# Se eliminó la clase Entrenamiento

class Reserva(models.Model):
    codigo_registro = models.AutoField(primary_key=True)
    usuario_solicitante = models.CharField(max_length=100)
    hora_prestamo = models.TimeField()
    fecha_entrada = models.DateField()
    hora_entrada = models.TimeField()
    fecha_permanencia = models.DateField()
    hora_salida = models.TimeField()
    fecha_salida = models.DateField()
    # Se eliminó el campo ForeignKey a Entrenamiento
    estado = models.CharField(max_length=20, default='Pendiente')

    def __str__(self):
        return f"{self.usuario_solicitante} - {self.fecha_entrada}"
    

class GimnasioConfig(models.Model):
    ESTADO_CHOICES = [
        ('abierta', 'Sala Abierta'),
        ('cerrada', 'Sala Cerrada'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    estado           = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierta')
    dias_habilitados = models.JSONField(default=list)
    horario_apertura = models.TimeField(default='07:00')
    horario_cierre   = models.TimeField(default='17:00')
    capacidad_maxima = models.PositiveIntegerField(default=40)
    actualizado_por  = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    actualizado_en   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del Gimnasio'

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def __str__(self):
        return f"Config Gimnasio — {self.estado}"


class FechaIngreso(models.Model):
    config      = models.ForeignKey(GimnasioConfig, on_delete=models.CASCADE, related_name='fechas')
    fecha       = models.DateField()
    descripcion = models.CharField(max_length=200, blank=True)
    habilitada  = models.BooleanField(default=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Fecha de Ingreso'

    def __str__(self):
        return str(self.fecha)