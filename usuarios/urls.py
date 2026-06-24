from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/',    views.login_view,    name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/',   views.logout_view,   name='logout'),
    path('perfil/',   views.perfil_view,   name='perfil'),

    # ─── GESTIÓN DE USUARIOS (página propia, solo admin) ───────────────────────
    path('usuarios/', views.gestionar_usuarios_view, name='gestionar_usuarios'),

    # ─── ACCIONES DE USUARIO (llamadas desde gestionar_usuarios) ───────────────
    path('perfil/toggle/<int:user_id>/',
         views.toggle_usuario_estado, name='toggle_usuario'),
    path('perfil/rol/<int:user_id>/',
         views.cambiar_rol_usuario,   name='cambiar_rol'),
    path('perfil/editar-usuario/<int:user_id>/',
         views.admin_editar_usuario,  name='admin_editar_usuario'),

    # ─── RECUPERACIÓN DE CONTRASEÑA (funciona con cualquier correo) ────────────
    # 1. Formulario donde el usuario ingresa su correo
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset.html',
             email_template_name='usuarios/emails/password_reset_email.html',
             subject_template_name='usuarios/emails/password_reset_subject.txt',
             success_url='/password-reset/enviado/',
         ),
         name='password_reset'),

    # 2. Confirmación: "Te enviamos el correo"
    path('password-reset/enviado/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_sent.html',
         ),
         name='password_reset_done'),

    # 3. El enlace del correo llega aquí → formulario nueva contraseña
    path('password-reset/confirmar/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html',
             success_url='/password-reset/listo/',
         ),
         name='password_reset_confirm'),

    # 4. Éxito: contraseña cambiada
    path('password-reset/listo/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
