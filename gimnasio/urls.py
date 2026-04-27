from django.urls import path
from . import views

urlpatterns = [
    path('', views.gimnasio_list, name='gimnasio'),
    path('eliminar-reserva/<int:id>/', views.eliminar_reserva, name='eliminar_reserva'),
    path('editar-reserva/<int:id>/', views.editar_reserva, name='editar_reserva'),
   
]