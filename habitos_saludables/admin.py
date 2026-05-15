"""
admin.py - Panel Administrativo del módulo Hábitos Saludables SENA
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    HabitoSaludable, RutinaFisica, PiramideNutricional,
    MaterialApoyo, SeguimientoSalud, HabeasDataConsent
)


@admin.register(HabeasDataConsent)
class HabeasDataConsentAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'acepta_badge', 'fecha_aceptacion', 'direccion_ip', 'version_politica']
    list_filter = ['acepta', 'version_politica']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['fecha_aceptacion', 'direccion_ip']
    ordering = ['-fecha_aceptacion']

    def acepta_badge(self, obj):
        if obj.acepta:
            return format_html('<span style="color:green;font-weight:bold">✓ Aceptado</span>')
        return format_html('<span style="color:red;font-weight:bold">✗ No aceptado</span>')
    acepta_badge.short_description = 'Estado'


@admin.register(HabitoSaludable)
class HabitoSaludableAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'activo', 'fecha_creacion']
    list_filter = ['categoria', 'activo']
    search_fields = ['titulo', 'descripcion']
    ordering = ['categoria', 'titulo']
    list_editable = ['activo']


@admin.register(RutinaFisica)
class RutinaFisicaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nivel', 'objetivo', 'duracion_minutos', 'activo']
    list_filter = ['nivel', 'objetivo', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nivel', 'objetivo']
    list_editable = ['activo']


@admin.register(PiramideNutricional)
class PiramideNutricionalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'nivel_piramide', 'cantidad_recomendada', 'activo']
    list_filter = ['categoria', 'nivel_piramide', 'activo']
    search_fields = ['nombre', 'beneficios', 'ejemplos']
    ordering = ['nivel_piramide', 'categoria']
    list_editable = ['activo']


@admin.register(MaterialApoyo)
class MaterialApoyoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_contenido', 'autor', 'fecha_publicacion', 'descargas', 'activo']
    list_filter = ['tipo_contenido', 'activo', 'fecha_publicacion']
    search_fields = ['titulo', 'descripcion', 'autor']
    ordering = ['-fecha_publicacion']
    readonly_fields = ['descargas']
    list_editable = ['activo']


@admin.register(SeguimientoSalud)
class SeguimientoSaludAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'fecha_evaluacion', 'peso_kg',
        'estatura_cm', 'imc_badge', 'nivel_actividad'
    ]
    list_filter = ['nivel_actividad', 'fecha_evaluacion']
    search_fields = ['usuario__username', 'usuario__first_name', 'observaciones']
    ordering = ['-fecha_evaluacion']
    readonly_fields = ['imc']

    def imc_badge(self, obj):
        if not obj.imc:
            return '—'
        imc = float(obj.imc)
        if imc < 18.5:
            color = 'orange'
        elif imc <= 24.9:
            color = 'green'
        elif imc <= 29.9:
            color = 'darkorange'
        else:
            color = 'red'
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>',
            color, obj.imc
        )
    imc_badge.short_description = 'IMC'