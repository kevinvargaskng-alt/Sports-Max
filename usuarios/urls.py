from django.urls import path
from . import views

urlpatterns = [
    path('login/',    views.login_view,    name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/',   views.logout_view,   name='logout'),
    path('perfil/',   views.perfil_view,   name='perfil'),

    # Solo admins (is_staff). Se llaman desde el tab de usuarios en perfil.
    path('perfil/toggle/<int:user_id>/',  views.toggle_usuario_estado, name='toggle_usuario'),
    path('perfil/rol/<int:user_id>/',     views.cambiar_rol_usuario,   name='cambiar_rol'),
    
    # NUEVA RUTA: Para la edición completa de usuarios por parte del administrador
    path('admin/editar-usuario/<int:user_id>/', views.admin_editar_usuario, name='admin_editar_usuario'),
]