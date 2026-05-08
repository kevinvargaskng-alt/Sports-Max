from django.urls import path
from . import views

urlpatterns = [
    # Vista principal Intercentros
    path('', views.intercentros_list, name='intercentros'),

    # Eliminar convocatoria (solo admin)
    path('eliminar/<int:id>/', views.eliminar_torneo, name='eliminar_torneo'),

    # Eliminar aviso (solo admin)
    path('aviso/eliminar/<int:id>/', views.eliminar_aviso, name='eliminar_aviso'),

    # ── Seleccionados SENA ──────────────────────────────────────────────────
    # Lista general de selecciones (admin gestiona / aprendiz consulta)
    path('seleccionados/', views.seleccionados_list, name='seleccionados'),

    # Detalle de una selección específica (gestión de miembros)
    path('seleccionados/<int:pk>/', views.detalle_seleccion, name='detalle_seleccion'),
]