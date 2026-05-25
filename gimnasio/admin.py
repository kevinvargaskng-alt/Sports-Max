# gimnasio/admin.py
# Registro en el panel de administración de Django

from django.contrib import admin
from .models import (
    ConfiguracionGimnasio, FechaEspecial, RegistroIngreso,
    Anamnesis, TestFisico, Rutina, EjercicioRutina,
)


@admin.register(ConfiguracionGimnasio)
class ConfiguracionGimnasioAdmin(admin.ModelAdmin):
    list_display = ['estado', 'horario_apertura', 'horario_cierre', 'capacidad_maxima', 'actualizado_en']
    readonly_fields = ['actualizado_en', 'actualizado_por']


@admin.register(FechaEspecial)
class FechaEspecialAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'descripcion', 'habilitada', 'creado_en']
    list_filter  = ['habilitada']


@admin.register(RegistroIngreso)
class RegistroIngresoAdmin(admin.ModelAdmin):
    list_display  = ['usuario', 'fecha_entrada', 'hora_entrada', 'creado_en']
    list_filter   = ['fecha_entrada']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'usuario__username']


@admin.register(Anamnesis)
class AnamnesisAdmin(admin.ModelAdmin):
    list_display  = ['usuario', 'peso_kg', 'talla_m', 'imc', 'clasificacion_imc', 'actualizado_en']
    readonly_fields = ['imc', 'clasificacion_imc', 'fecha_registro', 'actualizado_en']
    search_fields = ['usuario__first_name', 'usuario__last_name']


class EjercicioInline(admin.TabularInline):
    model  = EjercicioRutina
    extra  = 2
    fields = ['orden', 'nombre', 'maquina', 'series', 'repeticiones', 'duracion_min', 'peso_kg']


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'usuario', 'tipo', 'nivel', 'duracion_min', 'activa', 'creado_en']
    list_filter   = ['tipo', 'nivel', 'activa']
    search_fields = ['nombre', 'usuario__first_name', 'usuario__last_name']
    inlines       = [EjercicioInline]


@admin.register(TestFisico)
class TestFisicoAdmin(admin.ModelAdmin):
    list_display  = ['usuario', 'tipo', 'fecha', 'cooper_vo2max', 'cooper_categoria',
                     'ruffier_indice', 'ruffier_clasificacion']
    list_filter   = ['tipo', 'fecha']
    search_fields = ['usuario__first_name', 'usuario__last_name']
    readonly_fields = ['cooper_vo2max', 'cooper_categoria', 'ruffier_indice', 'ruffier_clasificacion']

