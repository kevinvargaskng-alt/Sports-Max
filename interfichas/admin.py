from django.contrib import admin
from .models import (Disciplina, TorneoInterfichas, EquipoInterfichas,
                     JugadorEquipo, GrupoInterfichas, PartidoInterfichas, ResultadoTorneo)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display  = ('nombre_disciplina', 'tipo_marcador')
    search_fields = ('nombre_disciplina',)


@admin.register(TorneoInterfichas)
class TorneoInterfichasAdmin(admin.ModelAdmin):
    list_display  = ('nombre_torneo', 'disciplina', 'estado', 'fecha_torneo_fichas', 'lugar')
    list_filter   = ('estado', 'disciplina')
    search_fields = ('nombre_torneo',)


@admin.register(EquipoInterfichas)
class EquipoAdmin(admin.ModelAdmin):
    list_display  = ('nombre_equipo', 'torneo', 'ficha', 'capitan', 'estado')
    list_filter   = ('estado', 'torneo')
    search_fields = ('nombre_equipo', 'capitan')


@admin.register(JugadorEquipo)
class JugadorAdmin(admin.ModelAdmin):
    list_display  = ('nombre_completo', 'equipo')
    search_fields = ('nombre_completo',)


@admin.register(GrupoInterfichas)
class GrupoAdmin(admin.ModelAdmin):
    list_display  = ('nombre_grupo', 'torneo')
    list_filter   = ('torneo',)


@admin.register(PartidoInterfichas)
class PartidoAdmin(admin.ModelAdmin):
    list_display  = ('equipo_local', 'equipo_visitante', 'torneo', 'fase', 'fecha_partido', 'jugado')
    list_filter   = ('jugado', 'fase', 'torneo')


@admin.register(ResultadoTorneo)
class ResultadoTorneoAdmin(admin.ModelAdmin):
    list_display  = ('torneo', 'ganador', 'fecha_cierre', 'archivado')
    list_filter   = ('archivado',)