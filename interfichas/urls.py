from django.urls import path
from . import views

urlpatterns = [
    # ── Vista principal unificada (admin + aprendiz) ───────────────
    path('',                                    views.interfichas_list,
         name='interfichas'),

    # ── Acciones de torneo (solo admin) ────────────────────────────
    path('torneo/<int:id>/editar/',
         views.editar_torneo,         name='editar_torneo'),
    path('torneo/<int:id>/eliminar/',
         views.eliminar_torneo,       name='eliminar_torneo'),
    path('torneo/<str:codigo_torneo>/cerrar/',
         views.cerrar_torneo,         name='cerrar_torneo'),

    # ── Gestión interna del torneo ─────────────────────────────────
    path('torneo/<int:torneo_id>/',
         views.gestionar_torneo,      name='gestionar_torneo'),
    path('torneo/<int:torneo_id>/grupos/',
         views.generar_grupos,        name='generar_grupos'),
    path('torneo/<int:torneo_id>/cuartos/',
         views.generar_cuartos,       name='generar_cuartos'),
    path('torneo/<int:torneo_id>/siguiente/',
         views.generar_siguiente_fase, name='generar_siguiente_fase'),
    path('torneo/<int:torneo_id>/reporte/',
         views.reporte_torneo,        name='reporte_torneo'),
    path('torneo/<int:torneo_id>/asignar-paises/',
         views.asignar_paises_torneo, name='asignar_paises_torneo'),

    # ── Partidos ───────────────────────────────────────────────────
    path('partido/<int:partido_id>/resultado/',
         views.registrar_resultado,   name='registrar_resultado'),
    path('partido/<int:partido_id>/fecha/',
         views.asignar_fecha_partido, name='asignar_fecha_partido'),
    path('torneo/<int:torneo_id>/grupos/manual/',
         views.generar_grupos_manual, name='generar_grupos_manual'),
    # ── Equipos ────────────────────────────────────────────────────
    path('equipo/<int:equipo_id>/editar/',
         views.editar_equipo,         name='editar_equipo'),
    path('equipo/<int:equipo_id>/eliminar/',
         views.eliminar_equipo,       name='eliminar_equipo'),
]
