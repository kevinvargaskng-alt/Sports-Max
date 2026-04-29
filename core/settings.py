import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv  # <--- NUEVO: Importamos dotenv para leer el archivo .env

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# <--- NUEVO: Cargar las variables del archivo .env al sistema --->
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SEGURIDAD: ¡Mantén esta clave en secreto en producción!
SECRET_KEY = 'django-insecure--+k6(v(s%fu$4wf6!f_n(=1*5(^txum^g-@4p8sxybqvna6g4x'

# SEGURIDAD: No uses DEBUG = True en producción
DEBUG = True

# CAMBIO: Se actualiza a la nueva IP y se mantiene el comodín para mayor flexibilidad
ALLOWED_HOSTS = ['192.168.3.199', 'localhost', '127.0.0.1', '*']

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

EMAIL_HOST_USER = 'kevinvargaskng@gmail.com' 
EMAIL_HOST_PASSWORD = 'pows bgxm pmvc zxvz' 

DEFAULT_FROM_EMAIL = 'Gestión Deportiva <kevinvargaskng@gmail.com>'

# ── SUGERENCIAS DE UX Y SEGURIDAD ────────────────────────

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 7200

# ── CONFIGURACIÓN DE INTELIGENCIA ARTIFICIAL (GEMINI) ────
# <--- NUEVO: Obtenemos la API key protegida desde tu archivo .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")