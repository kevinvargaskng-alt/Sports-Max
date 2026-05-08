from django.contrib import admin
from .models import ElementoDeportivo, Prestamo, DetallePrestamo, Devolucion, Sancion, Revision

@admin.register(ElementoDeportivo)
class ElementoAdmin(admin.ModelAdmin):
    # 'tipo_maquina' ahora es 'nombre_elemento'
    # 'docente_responsable' ahora es 'usuario_responsable'
    list_display  = ('nombre_elemento', 'cantidad_total', 'estado_general', 'usuario_responsable', 'fecha_adquisicion')
    list_filter   = ('estado_general',)
    search_fields = ('nombre_elemento', 'usuario_responsable__username') # usuario_responsable es FK, buscamos por su username

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    # Eliminamos 'elemento' porque ya no existe en Prestamo (está en DetallePrestamo)
    # 'fecha_devolucion' ahora es 'dia_devolucion'
    list_display  = ('usuario', 'cantidad_prestada', 'fecha_prestamo', 'dia_devolucion', 'estado_prestamo')
    list_filter   = ('estado_prestamo',)
    search_fields = ('usuario__username', 'usuario__first_name')

@admin.register(DetallePrestamo)
class DetallePrestamoAdmin(admin.ModelAdmin):
    list_display  = ('prestamo', 'elemento', 'fecha_devolucion', 'estado')
    list_filter   = ('estado',)

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display  = ('prestamo', 'cantidad_devuelta', 'fecha_devolucion', 'tiene_novedad', 'estado_elemento_devolucion')
    list_filter   = ('tiene_novedad', 'estado_elemento_devolucion')

@admin.register(Sancion)
class SancionAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'tipo_sancion', 'fecha_inicio_sancion', 'fecha_fin_sancion', 'estado_sancion')
    list_filter   = ('estado_sancion',)
    search_fields = ('usuario__username', 'usuario__first_name')

@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    # 'tipo_revision' ahora es 'tipo_novedad'
    list_display  = ('tipo_novedad', 'estado_resolucion', 'fecha_registro')
    list_filter   = ('estado_resolucion',)