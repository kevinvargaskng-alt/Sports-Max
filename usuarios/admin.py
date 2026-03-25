from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ('numero_documento', 'first_name', 'last_name', 'rol', 'estado', 'fecha_registro')
    search_fields = ('numero_documento', 'first_name', 'last_name')
    list_filter   = ('rol', 'estado', 'tipo_documento')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Adicionales', {
            'fields': ('numero_documento', 'tipo_documento', 'telefono', 'genero', 'rol', 'estado', 'foto_perfil')
        }),
    )