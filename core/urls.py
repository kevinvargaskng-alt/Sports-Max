from django.contrib import admin
from django.urls import path, include
# Importante para las vistas de clave
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# --- IMPORTACIÓN DE LA VISTA DEL AGENTE IA (NUEVO) ---
from core.views import chat_tux_api

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inicio
    path('', include('inicio.urls')),        # name='home'

    # Usuarios (login, logout, registro, perfil)
    path('', include('usuarios.urls')),      # /login/, /registro/, /perfil/

    # NOTA: El flujo de recuperación de contraseña está definido en usuarios/urls.py

    # Módulos deportivos
    path('interfichas/', include('interfichas.urls')),
    path('gimnasio/', include('gimnasio.urls')),
    path('inventario/', include('inventario.urls')),
    path('habitos/', include('habitos_saludables.urls')),

    # --- RUTA DEL AGENTE INTELIGENTE TUX (NUEVO) ---
    path('api/chat-tux/', chat_tux_api, name='chat_tux_api'),

]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
