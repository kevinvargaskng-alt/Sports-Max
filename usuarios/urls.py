from django.urls import path
from . import views

urlpatterns = [
    # Fíjate que ahora apuntan a _view, tal como en tu nuevo views.py
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'), 
    path('sugerencia/enviar/', views.enviar_sugerencia, name='enviar_sugerencia'),
]

