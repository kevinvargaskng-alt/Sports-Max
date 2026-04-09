from django.urls import path
from . import views

urlpatterns = [
    # Vista principal: Lista equipos, crea torneos e inscribe equipos
    path('', views.interfichas_list, name='interfichas'),
    
    # Eliminar torneo (Mantiene el parámetro <int:id>)
    path('eliminar/<int:id>/', views.eliminar_torneo, name='eliminar_torneo'),
    
    # Editar torneo (Cambio importante: No requiere ID en la URL si usas el modal)
    path('editar/', views.editar_torneo, name='editar_torneo'),
]