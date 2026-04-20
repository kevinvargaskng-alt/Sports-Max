import os
from pathlib import Path
from django.contrib.messages import constants as messages
from decouple import config

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: Variables de entorno desde .env
SECRET_KEY = config('SECRET_KEY')

# SEGURIDAD: No uses DEBUG = True en producción
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts permitidos desde .env
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tus aplicaciones
    'inicio',
    'interfichas',
    'intercentros',
    'gimnasio',
    'inventario',
    'usuarios', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.programas_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Base de datos (SQLite por defecto)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validadores de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización (Configurado para Colombia)
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Archivos Estáticos (CSS, JavaScript)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Archivos Multimedia (Fotos de perfil, inventario, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de campos automáticos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── AUTENTICACIÓN PERSONALIZADA ──────────────────────────
AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_URL = 'home'
LOGIN_REDIRECT_URL = 'perfil'
LOGOUT_REDIRECT_URL = 'home'

# ── CONFIGURACIÓN DE CORREO (GMAIL REAL) ─────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Variables de entorno desde .env
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD') 

# Nombre que aparecerá en el remitente del correo
DEFAULT_FROM_EMAIL = 'Gestión Deportiva <kevinvargaskng@gmail.com>'

# ── SUGERENCIAS DE UX Y SEGURIDAD ────────────────────────

# Mapeo de mensajes de Django a clases de Bootstrap 5
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# La sesión expira al cerrar el navegador (Seguridad para equipos compartidos)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Tiempo de vida de la sesión (2 horas)
SESSION_COOKIE_AGE = 7200