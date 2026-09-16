from django.contrib import admin
from django.urls import path, include
# Importante para las vistas de clave
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# --- IMPORTACIÓN DE LA VISTA DEL AGENTE IA (NUEVO) ---
from core.views import chat_tux_api, transcribe_voice_api
from gimnasio.views import (
    api_aforo_turnos,
    crear_reserva_turno,
    admin_franjas_list_create,
    admin_franja_editar,
    admin_franja_eliminar
)

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

    # --- ENDPOINTS GIMNASIO, TURNOS Y FRANJAS (CP-17, CP-18, CP-19) ---
    path('aforo/', api_aforo_turnos, name='aforo_global'),
    path('reserva/turno/', crear_reserva_turno, name='reserva_turno_global'),
    path('gimnasio/admin/franjas/', admin_franjas_list_create, name='admin_franjas_directo'),
    path('gimnasio/admin/franjas/editar/<int:pk>/', admin_franja_editar, name='admin_franja_editar_directo'),
    path('gimnasio/admin/franjas/eliminar/<int:pk>/', admin_franja_eliminar, name='admin_franja_eliminar_directo'),

    # --- RUTA DEL AGENTE INTELIGENTE TUX (NUEVO) ---
    path('api/chat-tux/', chat_tux_api, name='chat_tux_api'),
    path('api/transcribe-voice/', transcribe_voice_api, name='transcribe_voice_api'),

]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# ── Error Handlers — mensajes genéricos, stack traces solo en logs ──
handler400 = 'core.security.error_handlers.handler400'
handler403 = 'core.security.error_handlers.handler403'
handler404 = 'core.security.error_handlers.handler404'
handler500 = 'core.security.error_handlers.handler500'
