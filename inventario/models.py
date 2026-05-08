from django.db import models
from django.conf import settings

# 1. ELEMENTO DEPORTIVO
class ElementoDeportivo(models.Model):
    codigo_elemento = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to='elementos/', null=True, blank=True)
    tipo_maquina = models.CharField(max_length=100)
    cantidad_total = models.IntegerField(default=0)
    estado_general = models.CharField(max_length=50)
    fecha_adquisicion = models.DateField()
    descripcion = models.TextField(blank=True)
    
    # CORRECCIÓN 1: De CharField a ForeignKey (Vínculo real con USUARIOS)
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='elementos_a_cargo'
    )

    def __str__(self):
        return self.tipo_maquina

# 2. PRESTAMO (Cabecera)
class Prestamo(models.Model):
    codigo_prestamo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prestamos_realizados'
    )
    # CORRECCIÓN 2: Se elimina 'elemento' de aquí porque el MER dice que 
    # un préstamo puede tener MUCHOS elementos (vía DetallePrestamo).
    fecha_prestamo = models.DateField(auto_now_add=True)
    hora_prestamo = models.TimeField(auto_now_add=True)
    dias_prestamo = models.IntegerField(default=1)
    estado_prestamo = models.CharField(max_length=30, default='Activo')
    observacion_prestamo = models.TextField(blank=True)

    def __str__(self):
        return f"Préstamo #{self.codigo_prestamo} - {self.usuario.username}"

# 3. DETALLE PRESTAMO (Relación M:M)
class DetallePrestamo(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='detalles')
    elemento = models.ForeignKey(ElementoDeportivo, on_delete=models.CASCADE)
    fecha_devolucion_prevista = models.DateField() # Renombrado para claridad
    estado = models.CharField(max_length=30, default='Pendiente')

    def __str__(self):
        return f"Detalle #{self.id_detalle} - {self.elemento.tipo_maquina}"

# 4. DEVOLUCION
class Devolucion(models.Model):
    codigo_devolucion = models.AutoField(primary_key=True)
    # CORRECCIÓN 3: Relación 1:1 o ForeignKey con Préstamo
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='devoluciones')
    fecha_devolucion = models.DateField(auto_now_add=True)
    hora_devolucion = models.TimeField(auto_now_add=True)
    observaciones_devolucion = models.TextField(blank=True)

    def __str__(self):
        return f"Devolución #{self.codigo_devolucion} del Préstamo {self.prestamo.codigo_prestamo}"

# 5. REVISION
class Revision(models.Model):
    codigo_revision = models.AutoField(primary_key=True)
    # CORRECCIÓN 4: Vincular con Devolución como dice el MER
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='revisiones', null=True)
    
    # CORRECCIÓN 5: Nombres de campos idénticos al MER
    tipo_novedad = models.CharField(max_length=100) 
    descripcion_detallada = models.TextField(blank=True)
    
    estado_resolucion = models.CharField(max_length=30, default='Pendiente')
    fecha_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Revisión #{self.codigo_revision} - {self.tipo_novedad}"

# 6. SANCION
class Sancion(models.Model):
    codigo_sancion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sanciones'
    )
    # CORRECCIÓN 6: Vincular con la devolución que originó la sanción
    devolucion = models.ForeignKey(Devolucion, on_delete=models.SET_NULL, null=True, blank=True)
    
    tipo_sancion = models.CharField(max_length=100)
    fecha_inicio_sancion = models.DateField()
    fecha_fin_sancion = models.DateField()
    estado_sancion = models.CharField(max_length=30, default='Activa')
    descripcion_sancion = models.TextField(blank=True)

    def __str__(self):
        return f"Sanción a {self.usuario} - {self.tipo_sancion}"