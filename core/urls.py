from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inicio
    path('', include('inicio.urls')),        # name='home'

    # Usuarios (login, logout, registro, perfil)
    path('', include('usuarios.urls')),      # ← sin prefijo para que /login/ /registro/ /perfil/ funcionen directo

    # Módulos deportivos
    path('interfichas/', include('interfichas.urls')),
    path('intercentros/', include('intercentros.urls')),
    path('gimnasio/', include('gimnasio.urls')),
    path('inventario/', include('inventario.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)