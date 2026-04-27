from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal
    path('', views.intercentros_list, name='intercentros'),
    
    # Ruta para eliminar (Asegúrate que en views.py se llame eliminar_torneo)
    path('eliminar/<int:id>/', views.eliminar_torneo, name='eliminar_torneo'),
    
    # ELIMINAMOS la ruta de editar porque no la estamos usando en el views actual
]