"""
urls.py - Rutas del módulo Hábitos Saludables SENA
Prefijo sugerido en el proyecto: path('habitos/', include('habitos_saludables.urls'))
"""

from django.urls import path
from . import views

app_name = 'habitos'

urlpatterns = [

    # ── Inicio y dashboard ──────────────────────────
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Habeas Data ─────────────────────────────────
    path('habeas-data/', views.habeas_data, name='habeas_data'),

    # ── Hábitos saludables (contenido educativo) ────
    path('habitos/', views.lista_habitos, name='lista_habitos'),
    path('habitos/<int:pk>/', views.detalle_habito, name='detalle_habito'),

    # ── Rutinas físicas ──────────────────────────────
    path('rutinas/', views.lista_rutinas, name='lista_rutinas'),
    path('rutinas/<int:pk>/', views.detalle_rutina, name='detalle_rutina'),

    # ── Pirámide nutricional ─────────────────────────
    path('nutricion/', views.piramide_nutricional, name='nutricion'),

    # ── Biblioteca de materiales ─────────────────────
    path('biblioteca/', views.biblioteca, name='biblioteca'),
    path('biblioteca/descargar/<int:pk>/',
         views.descargar_material, name='descargar_material'),

    # ── Seguimiento de salud ─────────────────────────
    path('salud/registrar/', views.registrar_seguimiento,
         name='registrar_seguimiento'),
    path('salud/historial/', views.historial_salud, name='historial_salud'),
    path('salud/<int:pk>/', views.detalle_seguimiento, name='detalle_seguimiento'),
    path('salud/<int:pk>/eliminar/', views.eliminar_seguimiento,
         name='eliminar_seguimiento'),
]
