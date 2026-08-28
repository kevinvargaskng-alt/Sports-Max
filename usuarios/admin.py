from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Sugerencia, HistorialAccion



@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('numero_documento', 'first_name',
                    'last_name', 'rol', 'estado', 'fecha_registro', 'fecha_actualizacion', 'last_login')
    search_fields = ('numero_documento', 'first_name', 'last_name', 'email')
    list_filter = ('rol', 'estado', 'tipo_documento')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion', 'last_login')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Adicionales', {
            'fields': ('numero_documento', 'tipo_documento', 'telefono', 'genero', 'rol', 'estado', 'foto_perfil', 'ficha', 'programa_formacion', 'fecha_registro', 'fecha_actualizacion')
        }),
    )


@admin.register(Sugerencia)
class SugerenciaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'get_usuario', 'tipo', 'respondido')
    list_filter = ('tipo', 'anonimo')
    readonly_fields = ('usuario', 'tipo', 'comentario', 'fecha')

    def get_usuario(self, obj):
        return "Anónimo" if obj.anonimo else obj.usuario
    get_usuario.short_description = "Remitente"

    def respondido(self, obj):
        return bool(obj.respuesta)
    respondido.boolean = True


@admin.register(HistorialAccion)
class HistorialAccionAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'modulo', 'accion', 'ip_origen')
    list_filter = ('modulo', 'fecha')
    search_fields = ('usuario__username', 'accion', 'descripcion', 'ip_origen')
    readonly_fields = ('public_id', 'usuario', 'modulo', 'accion', 'descripcion', 'ip_origen', 'fecha')

    def has_add_permission(self, request):
        return False  # El historial solo se genera automáticamente por el sistema

