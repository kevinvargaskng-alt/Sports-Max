from django.contrib import admin
from .models import Reserva, GimnasioConfig


@admin.register(GimnasioConfig)
class GimnasioConfigAdmin(admin.ModelAdmin):
    list_display = ('estado', 'horario_apertura',
                    'horario_cierre', 'capacidad_maxima')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario_solicitante', 'fecha_entrada',
                    'hora_entrada', 'hora_salida', 'estado')
    list_filter = ('estado', 'fecha_entrada')
    search_fields = ('usuario_solicitante',)
