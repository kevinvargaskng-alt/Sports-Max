from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importante para las vistas de clave
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inicio
    path('', include('inicio.urls')),        # name='home'

    # Usuarios (login, logout, registro, perfil)
    path('', include('usuarios.urls')),      # /login/, /registro/, /perfil/

    # --- FLUJO DE RECUPERACIÓN DE CONTRASEÑA (NUEVO) ---
    # 1. El usuario solicita el reset
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="usuarios/registration/password_reset.html"), 
         name="password_reset"),

    # 2. Confirmación de correo enviado
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="usuarios/registration/password_reset_sent.html"), 
         name="password_reset_done"),

    # 3. El enlace que llega al correo (ID de usuario + Token de seguridad)
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="usuarios/registration/password_reset_confirm.html"), 
         name="password_reset_confirm"),

    # 4. Mensaje de éxito final
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="usuarios/registration/password_reset_complete.html"), 
         name="password_reset_complete"),
    # --------------------------------------------------

    # Módulos deportivos
    path('interfichas/', include('interfichas.urls')),
    path('intercentros/', include('intercentros.urls')),
    path('gimnasio/', include('gimnasio.urls')),
    path('inventario/', include('inventario.urls')),

]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)