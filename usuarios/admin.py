from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Sugerencia


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('numero_documento', 'first_name',
                    'last_name', 'rol', 'estado', 'fecha_registro')
    search_fields = ('numero_documento', 'first_name', 'last_name')
    list_filter = ('rol', 'estado', 'tipo_documento')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Adicionales', {
            'fields': ('numero_documento', 'tipo_documento', 'telefono', 'genero', 'rol', 'estado', 'foto_perfil', 'ficha', 'programa_formacion')
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
