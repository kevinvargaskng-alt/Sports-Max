from django.contrib import admin
from .models import (
    TorneoIntercentros, EquipoIntercentros,
    Postulacion, Entrenamiento, AsistenciaEntrenamiento,
    Aviso, SeleccionadoSena, MiembroSeleccionado,
)


@admin.register(TorneoIntercentros)
class TorneoIntercentrosAdmin(admin.ModelAdmin):
    list_display  = ('nombre_torneo', 'disciplina', 'estado', 'fecha_torneo', 'lugar')
    list_filter   = ('estado', 'disciplina')
    search_fields = ('nombre_torneo',)


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display  = ('nombres', 'apellidos', 'numero_documento', 'ficha', 'disciplina', 'torneo', 'fecha_postulacion')
    search_fields = ('nombres', 'apellidos', 'numero_documento')
    list_filter   = ('torneo', 'disciplina')


@admin.register(Entrenamiento)
class EntrenamientoAdmin(admin.ModelAdmin):
    list_display  = ('disciplina', 'torneo', 'fecha', 'hora', 'lugar')
    list_filter   = ('disciplina', 'torneo')
    search_fields = ('disciplina', 'lugar')


@admin.register(AsistenciaEntrenamiento)
class AsistenciaEntrenamientoAdmin(admin.ModelAdmin):
    list_display  = ('nombres', 'apellidos', 'numero_documento', 'ficha', 'entrenamiento', 'confirmado_en')
    list_filter   = ('entrenamiento',)
    search_fields = ('nombres', 'apellidos', 'numero_documento')


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'tipo', 'disciplina', 'torneo', 'creado_en')
    list_filter   = ('tipo', 'disciplina', 'torneo')
    search_fields = ('titulo', 'cuerpo')


# ── Inline de miembros dentro de la selección ─────────────────────────────────

class MiembroSeleccionadoInline(admin.TabularInline):
    model         = MiembroSeleccionado
    extra         = 0
    fields        = ('nombres', 'apellidos', 'numero_documento', 'ficha', 'disciplina', 'seleccionado_en')
    readonly_fields = ('seleccionado_en',)
    can_delete    = True


@admin.register(SeleccionadoSena)
class SeleccionadoSenaAdmin(admin.ModelAdmin):
    list_display   = (
        '__str__', 'torneo', 'disciplina',
        'estado_seleccion', 'capacidad', 'total_miembros',
        'fecha_seleccion', 'estado'
    )
    list_filter    = ('estado_seleccion', 'disciplina', 'estado', 'torneo')
    search_fields  = ('disciplina', 'torneo__nombre_torneo')
    inlines        = [MiembroSeleccionadoInline]
    readonly_fields = ('creado_en',)

    @admin.display(description='Seleccionados')
    def total_miembros(self, obj):
        return f"{obj.miembros.count()} / {obj.capacidad}"


@admin.register(MiembroSeleccionado)
class MiembroSeleccionadoAdmin(admin.ModelAdmin):
    list_display  = ('nombres', 'apellidos', 'numero_documento', 'ficha', 'disciplina', 'seleccion', 'seleccionado_en')
    list_filter   = ('seleccion', 'disciplina')
    search_fields = ('nombres', 'apellidos', 'numero_documento')