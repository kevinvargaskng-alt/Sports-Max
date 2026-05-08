from django.db import models
from django.conf import settings


class ElementoDeportivo(models.Model):
    codigo_elemento = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to='elementos/', null=True, blank=True)
    nombre_elemento = models.CharField(max_length=100)           # era: tipo_maquina
    cantidad_total = models.IntegerField(default=0)
    estado_general = models.CharField(max_length=50)
    fecha_adquisicion = models.DateField()
    descripcion = models.TextField(blank=True)
    usuario_responsable = models.ForeignKey(                     # era: docente_responsable (CharField)
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='elementos_a_cargo',
        limit_choices_to={'is_staff': True},
    )

    def __str__(self):
        return self.nombre_elemento


class Prestamo(models.Model):
    codigo_prestamo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prestamos_realizados',
        null=True,
        blank=True,
    )
    # ─── eliminada la FK directa a elemento: los elementos van en DetallePrestamo ───
    fecha_prestamo = models.DateField(auto_now_add=True)
    hora_prestamo = models.TimeField(auto_now_add=True)
    dias_prestamo = models.IntegerField(default=1)
    dia_devolucion = models.DateField()                          # era: fecha_devolucion
    cantidad_prestada = models.IntegerField(default=1)
    estado_prestamo = models.CharField(max_length=30, default='Activo')
    observacion_prestamo = models.TextField(blank=True)

    def __str__(self):
        return f"Préstamo #{self.codigo_prestamo}"


class DetallePrestamo(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='detalles')
    elemento = models.ForeignKey(ElementoDeportivo, on_delete=models.CASCADE)
    fecha_devolucion = models.DateField()
    estado = models.CharField(max_length=30, default='Pendiente')
    prestamos_usuarios_aprendiz = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Detalle #{self.id_detalle} — {self.elemento.nombre_elemento}"


class Devolucion(models.Model):
    codigo_devolucion = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='devoluciones')
    cantidad_devuelta = models.IntegerField(default=1)
    fecha_devolucion = models.DateField()
    hora_devolucion = models.TimeField()
    tiene_novedad = models.BooleanField(default=False)
    estado_elemento_devolucion = models.CharField(max_length=50)
    tipo_novedad_devolucion = models.CharField(max_length=100, blank=True)
    observaciones_devolucion = models.TextField(blank=True)
    dias_retraso = models.IntegerField(default=0)                # campo que estaba en el MER

    def __str__(self):
        return f"Devolución #{self.codigo_devolucion}"


class Revision(models.Model):
    codigo_revision = models.AutoField(primary_key=True)
    devolucion = models.ForeignKey(                              # FK que faltaba al MER
        Devolucion,
        on_delete=models.CASCADE,
        related_name='revisiones',
        null=True,
        blank=True,
    )
    tipo_novedad = models.CharField(max_length=100)              # era: tipo_revision
    descripcion_detallada = models.TextField(blank=True)         # era: revision_detallada
    estado_resolucion = models.CharField(max_length=30, default='Pendiente')
    fecha_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_novedad} - {self.estado_resolucion}"


class Sancion(models.Model):
    codigo_sancion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sanciones',
        null=True,
        blank=True,
    )
    devolucion = models.ForeignKey(                              # FK que faltaba al MER
        Devolucion,
        on_delete=models.SET_NULL,
        related_name='sanciones',
        null=True,
        blank=True,
    )
    tipo_sancion = models.CharField(max_length=100)
    fecha_inicio_sancion = models.DateField()
    fecha_fin_sancion = models.DateField()
    estado_sancion = models.CharField(max_length=30, default='Activa')
    descripcion_sancion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tipo_sancion} - {self.estado_sancion}"