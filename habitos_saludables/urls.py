"""
urls.py - Rutas del módulo Hábitos Saludables SENA
Prefijo en el proyecto: path('habitos/', include('habitos_saludables.urls'))
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

    # ── CP-11: Seguimiento de rutinas del usuario ────
    path('mis-rutinas/', views.mis_rutinas, name='mis_rutinas'),
    path('api/registrar-sesion/', views.registrar_sesion, name='registrar_sesion'),

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

    # ── CP-10: Cálculo de IMC y calorías ────────────
    path('calcular-imc/', views.vista_calcular_imc, name='calcular_imc'),
    path('api/calcular-imc/', views.calcular_imc_api, name='calcular_imc_api'),

    # ── CP-13: Recetas saludables ────────────────────
    path('recetas/', views.lista_recetas, name='lista_recetas'),
    path('recetas/nueva/', views.crear_receta, name='crear_receta'),
    path('recetas/<int:pk>/', views.detalle_receta, name='detalle_receta'),
    path('recetas/<int:pk>/editar/', views.editar_receta, name='editar_receta'),

    # ── CP-15: Gráfica de sueño semanal ─────────────
    path('sueno/', views.grafica_sueno, name='grafica_sueno'),
    path('api/sueno-semanal/', views.api_sueno_semanal, name='api_sueno_semanal'),
    path('api/registrar-sueno/', views.registrar_sueno, name='registrar_sueno'),

    # ── CP-12: Notificaciones push ───────────────────
    path('notificaciones/', views.configurar_notificaciones, name='configurar_notificaciones'),
    path('api/guardar-suscripcion/', views.guardar_suscripcion_push, name='guardar_suscripcion'),

    # ── CP-14: Dashboard de progreso ─────────────────
    path('mi-progreso/', views.dashboard_progreso, name='dashboard_progreso'),
]
