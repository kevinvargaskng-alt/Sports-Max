from django.contrib import admin
from .models import ElementoDeportivo, Prestamo, DetallePrestamo, Devolucion, Revision, Sancion

# Configuración para ver los elementos dentro del formulario de préstamo


class DetallePrestamoInline(admin.TabularInline):
    model = DetallePrestamo
    extra = 1


@admin.register(ElementoDeportivo)
class ElementoAdmin(admin.ModelAdmin):
    list_display = ('tipo_maquina', 'cantidad_total',
                    'estado_general', 'usuario_responsable')
    search_fields = ('tipo_maquina',)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('codigo_prestamo', 'usuario',
                    'fecha_prestamo', 'estado_prestamo')
    list_filter = ('estado_prestamo', 'fecha_prestamo')
    inlines = [DetallePrestamoInline]


@admin.register(DetallePrestamo)
class DetallePrestamoAdmin(admin.ModelAdmin):
    list_display = ('id_detalle', 'prestamo', 'elemento',
                    'fecha_devolucion_prevista', 'estado')


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('codigo_devolucion', 'prestamo',
                    'fecha_devolucion', 'hora_devolucion')
    list_filter = ('fecha_devolucion',)


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ('codigo_revision', 'devolucion',
                    'tipo_novedad', 'estado_resolucion')
    list_filter = ('estado_resolucion', 'tipo_novedad')


@admin.register(Sancion)
class SancionAdmin(admin.ModelAdmin):
    list_display = ('codigo_sancion', 'usuario',
                    'tipo_sancion', 'estado_sancion')
    list_filter = ('estado_sancion',)
