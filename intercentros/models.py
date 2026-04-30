from django.db import models
from django.conf import settings


class TorneoIntercentros(models.Model):
    codigo_torneo_centro = models.AutoField(primary_key=True)
    nombre_torneo        = models.CharField(max_length=100)
    fecha_torneo         = models.DateField()
    lugar                = models.CharField(max_length=100)
    disciplina           = models.CharField(max_length=50)
    estado               = models.CharField(max_length=20, default='Activo')

    def __str__(self):
        return self.nombre_torneo


class EquipoIntercentros(models.Model):
    codigo_equipo_centro = models.AutoField(primary_key=True)
    nombre_equipo        = models.CharField(max_length=100)
    disciplina           = models.CharField(max_length=50)
    fecha_creacion       = models.DateField(auto_now_add=True)
    torneo               = models.ForeignKey(
        TorneoIntercentros, on_delete=models.CASCADE, related_name='equipos'
    )

    def __str__(self):
        return self.nombre_equipo


class Postulacion(models.Model):
    """Postulación de un aprendiz a una convocatoria Intercentros."""
    torneo             = models.ForeignKey(
        TorneoIntercentros, on_delete=models.CASCADE, related_name='postulaciones'
    )
    numero_documento   = models.CharField(max_length=20)
    nombres            = models.CharField(max_length=100)
    apellidos          = models.CharField(max_length=100)
    ficha              = models.CharField(max_length=20, blank=True)
    programa_formacion = models.CharField(max_length=150, blank=True)
    disciplina         = models.CharField(max_length=50)
    fecha_postulacion  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('torneo', 'numero_documento')

    def __str__(self):
        return f"{self.nombres} {self.apellidos} → {self.torneo}"


class Entrenamiento(models.Model):
    torneo      = models.ForeignKey(
        TorneoIntercentros, on_delete=models.CASCADE,
        related_name='entrenamientos', null=True, blank=True
    )
    disciplina  = models.CharField(max_length=50)
    fecha       = models.DateField()
    hora        = models.TimeField()
    lugar       = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.disciplina} – {self.fecha} {self.hora}"


class AsistenciaEntrenamiento(models.Model):
    """Confirmación de asistencia de un aprendiz a un entrenamiento."""
    entrenamiento    = models.ForeignKey(
        Entrenamiento, on_delete=models.CASCADE, related_name='asistencias'
    )
    numero_documento = models.CharField(max_length=20)
    nombres          = models.CharField(max_length=100, blank=True)
    apellidos        = models.CharField(max_length=100, blank=True)
    ficha            = models.CharField(max_length=20, blank=True)
    confirmado_en    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('entrenamiento', 'numero_documento')
        verbose_name        = 'Asistencia a Entrenamiento'
        verbose_name_plural = 'Asistencias a Entrenamientos'
        ordering            = ['nombres', 'apellidos']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} → {self.entrenamiento}"


class Aviso(models.Model):
    TIPO_CHOICES = [
        ('info',   'Información'),
        ('alerta', 'Alerta'),
        ('result', 'Resultado'),
    ]
    titulo     = models.CharField(max_length=150)
    cuerpo     = models.TextField()
    tipo       = models.CharField(max_length=10, choices=TIPO_CHOICES, default='info')
    disciplina = models.CharField(max_length=50, blank=True,
                                  help_text="Dejar en blanco para avisos generales")
    torneo     = models.ForeignKey(
        TorneoIntercentros, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='avisos'
    )
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return self.titulo


class SeleccionadorSena(models.Model):
    codigo_seleccionador = models.AutoField(primary_key=True)
    nombre_seleccion     = models.CharField(max_length=100)
    disciplina           = models.CharField(max_length=50)
    fecha_seleccion      = models.DateField()

    def __str__(self):
        return self.nombre_seleccion


class ParticipacionIntercentros(models.Model):
    codigo_participacion = models.AutoField(primary_key=True)
    torneo               = models.ForeignKey(TorneoIntercentros, on_delete=models.CASCADE)
    equipo               = models.ForeignKey(EquipoIntercentros, on_delete=models.CASCADE)
    fecha_juego          = models.DateField()
    puntaje              = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.equipo} - {self.torneo}"