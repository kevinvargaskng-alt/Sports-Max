from django.db import models
from django.conf import settings

# Punto 1: ElementoDeportivo
class ElementoDeportivo(models.Model):
    # Estos son los campos que tu Admin está pidiendo:
    tipo_maquina = models.CharField(max_length=100, verbose_name="Tipo de Máquina/Elemento")
    cantidad_total = models.IntegerField(default=1)
    estado_general = models.CharField(max_length=50, default='Buen estado')
    
    # El campo que ajustamos para el MER:
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        verbose_name="Usuario Responsable"
    )

    def __str__(self):
        return f"{self.tipo_maquina} - {self.estado_general}"
# Punto 6: RESERVA (¡Faltaba este modelo en tu código!)
class Reserva(models.Model):
    codigo_reserva = models.AutoField(primary_key=True)
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservas'
    )
    elemento = models.ForeignKey(ElementoDeportivo, on_delete=models.CASCADE)
    fecha_reserva = models.DateField()
    hora_reserva = models.TimeField()
    tiempo_permanencia = models.IntegerField(help_text="Duración en minutos")
    estado_reserva = models.CharField(max_length=30, default='Pendiente')

# 2. PRESTAMO (Cabecera) - ¡YA ESTÁ PERFECTO!
class Prestamo(models.Model):
    codigo_prestamo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prestamos_realizados'
    )
    fecha_prestamo = models.DateField(auto_now_add=True)
    hora_prestamo = models.TimeField(auto_now_add=True)
    dias_prestamo = models.IntegerField(default=1)
    estado_prestamo = models.CharField(max_length=30, default='Activo')
    observacion_prestamo = models.TextField(blank=True)

    def __str__(self):
        return f"Préstamo #{self.codigo_prestamo} - {self.usuario.username}"

# 3. DETALLE PRESTAMO - ¡YA ESTÁ PERFECTO!
class DetallePrestamo(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='detalles')
    elemento = models.ForeignKey(ElementoDeportivo, on_delete=models.CASCADE)
    fecha_devolucion_prevista = models.DateField()
    estado = models.CharField(max_length=30, default='Pendiente')

    def __str__(self):
        return f"Detalle #{self.id_detalle}"

# 4. DEVOLUCION - ¡YA ESTÁ PERFECTO!
class Devolucion(models.Model):
    codigo_devolucion = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='devoluciones')
    fecha_devolucion = models.DateField(auto_now_add=True)
    hora_devolucion = models.TimeField(auto_now_add=True)
    observaciones_devolucion = models.TextField(blank=True)

    def __str__(self):
        return f"Devolución #{self.codigo_devolucion}"

# 5. REVISION - ¡YA ESTÁ PERFECTO! (Alineado con nombres del MER)
class Revision(models.Model):
    codigo_revision = models.AutoField(primary_key=True)
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='revisiones', null=True)
    tipo_novedad = models.CharField(max_length=100) 
    descripcion_detallada = models.TextField(blank=True)
    estado_resolucion = models.CharField(max_length=30, default='Pendiente')
    fecha_registro = models.DateField(auto_now_add=True)

# 6. SANCION - ¡YA ESTÁ PERFECTO!
class Sancion(models.Model):
    codigo_sancion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sanciones'
    )
    devolucion = models.ForeignKey(Devolucion, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_sancion = models.CharField(max_length=100)
    fecha_inicio_sancion = models.DateField()
    fecha_fin_sancion = models.DateField()
    estado_sancion = models.CharField(max_length=30, default='Activa')
    descripcion_sancion = models.TextField(blank=True)