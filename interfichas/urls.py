from django.urls import path
from . import views

urlpatterns = [
    # Vista principal
    path('', views.interfichas_list, name='interfichas'),

    # CRUD Torneos
    path('eliminar/<int:id>/', views.eliminar_torneo, name='eliminar_torneo'),
    path('editar/', views.editar_torneo, name='editar_torneo'),

    # ── GESTIÓN COMPLETA DEL TORNEO ──────────────────────────────
    path('gestionar/<int:torneo_id>/', views.gestionar_torneo, name='gestionar_torneo'),

    # Generar grupos (POST)
    path('gestionar/<int:torneo_id>/generar-grupos/', views.generar_grupos, name='generar_grupos'),

    # Registrar resultado de un partido (POST)
    path('partido/<int:partido_id>/resultado/', views.registrar_resultado, name='registrar_resultado'),

    # Asignar fecha/hora a partido (POST)
    path('partido/<int:partido_id>/fecha/', views.asignar_fecha_partido, name='asignar_fecha_partido'),

    # Generar cuartos de final (POST)
    path('gestionar/<int:torneo_id>/generar-cuartos/', views.generar_cuartos, name='generar_cuartos'),

    # Generar semifinal o final (POST) — recibe fase_origen en body
    path('gestionar/<int:torneo_id>/siguiente-fase/', views.generar_siguiente_fase, name='generar_siguiente_fase'),
]