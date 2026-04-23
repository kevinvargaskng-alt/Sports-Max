from django.urls import path
from . import views

urlpatterns = [
    # Inventario principal
    path('', views.inventario_list, name='inventario'),

    # Elementos
    path('eliminar-elemento/<int:id>/', views.eliminar_elemento, name='eliminar_elemento'),
    path('editar-elemento/<int:id>/',   views.editar_elemento,   name='editar_elemento'),

    # Préstamos
    path('eliminar-prestamo/<int:id>/', views.eliminar_prestamo, name='eliminar_prestamo'),

    # Devoluciones
    path('devoluciones/', views.devoluciones_list, name='devoluciones'),

    # Sanciones
    path('sanciones/', views.sanciones_list, name='sanciones'),
]