from django.urls import path
from . import views

urlpatterns = [
    # El nombre debe ser 'home' porque así lo busca tu header.html
    path('', views.inicio, name='home'),
]
