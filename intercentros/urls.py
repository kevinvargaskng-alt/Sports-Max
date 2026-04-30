from django.urls import path
from . import views

urlpatterns = [
    # Vista principal
    path('', views.intercentros_list, name='intercentros'),

    # Eliminar convocatoria (solo admin)
    path('eliminar/<int:id>/', views.eliminar_torneo, name='eliminar_torneo'),

    # Eliminar aviso (solo admin)
    path('aviso/eliminar/<int:id>/', views.eliminar_aviso, name='eliminar_aviso'),
]