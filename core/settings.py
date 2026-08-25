import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))

# ═══════════════════════════════════════════════════════════
#  SEGURIDAD FUNDAMENTAL
# ═══════════════════════════════════════════════════════════

# La SECRET_KEY DEBE existir en .env — falla ruidosamente si no está
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "⛔ SEGURIDAD: SECRET_KEY no configurada en .env. "
        "Genera una con: python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )

# DEBUG controlado por variable de entorno (default: False = seguro)
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# ALLOWED_HOSTS desde .env — NUNCA usar '*' en producción
_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inicio',
    'interfichas',
    'gimnasio',
    'inventario',
    'usuarios',
    'habitos_saludables',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ── Middlewares de seguridad personalizados ────────────────
    'core.security.middleware.RateLimitMiddleware',
    'core.security.middleware.SecurityHeadersMiddleware',
    'core.security.middleware.AuditMiddleware',
    # ──────────────────────────────────────────────────────────
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

# ═══════════════════════════════════════════════════════════
#  BASE DE DATOS (dinámica: MySQL/PostgreSQL/SQLite)
# ═══════════════════════════════════════════════════════════
DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.mysql')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '3306')

if DB_NAME and DB_USER:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ═══════════════════════════════════════════════════════════
#  CONTRASEÑAS — Hash Argon2id + Validación robusta
# ═══════════════════════════════════════════════════════════

# Priorizar Argon2id sobre PBKDF2 (más resistente a GPU/ASIC)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    # ── Validadores personalizados de seguridad ───────────────
    {'NAME': 'core.security.password_validators.BreachedPasswordValidator'},
    {'NAME': 'core.security.password_validators.StrongPasswordValidator'},
    {'NAME': 'core.security.password_validators.NoPersonalInfoValidator'},
]

# ═══════════════════════════════════════════════════════════
#  INTERNACIONALIZACIÓN
# ═══════════════════════════════════════════════════════════
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ═══════════════════════════════════════════════════════════
#  ARCHIVOS ESTÁTICOS Y MEDIA
# ═══════════════════════════════════════════════════════════
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ── Límites de subida de archivos ─────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024    # 5 MB en memoria
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB total

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════════════
#  AUTENTICACIÓN Y SESIÓN
# ═══════════════════════════════════════════════════════════
AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_URL = 'home'
LOGIN_REDIRECT_URL = 'perfil'
LOGOUT_REDIRECT_URL = 'home'

# ── Sesión segura ─────────────────────────────────────────
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 7200                        # 2 horas
SESSION_COOKIE_HTTPONLY = True                    # No accesible por JavaScript
SESSION_COOKIE_SECURE = not DEBUG                 # Solo HTTPS en producción
SESSION_COOKIE_SAMESITE = 'Lax'                  # Protección CSRF
SESSION_SAVE_EVERY_REQUEST = True                 # Renovar expiración con actividad

# ── CSRF seguro ───────────────────────────────────────────
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'

# ── Cabeceras de seguridad (base Django) ──────────────────
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ═══════════════════════════════════════════════════════════
#  HTTPS / HSTS (solo producción)
# ═══════════════════════════════════════════════════════════
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000                # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ═══════════════════════════════════════════════════════════
#  EMAIL
# ═══════════════════════════════════════════════════════════
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')

# ═══════════════════════════════════════════════════════════
#  MESSAGES
# ═══════════════════════════════════════════════════════════
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ═══════════════════════════════════════════════════════════
#  RATE LIMITING (por IP)
# ═══════════════════════════════════════════════════════════
RATE_LIMIT_CONFIG = {
    'login':   {'rate': 5,   'period': 60},     # 5 req/min
    'api':     {'rate': 30,  'period': 60},     # 30 req/min
    'default': {'rate': 100, 'period': 60},     # 100 req/min
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'security-rate-limit',
    }
}

# ═══════════════════════════════════════════════════════════
#  MOTOR IA (sin API key externa)
# ═══════════════════════════════════════════════════════════
IA_SERVER_URL = os.environ.get('IA_SERVER_URL', 'http://127.0.0.1:5001')

# ═══════════════════════════════════════════════════════════
#  LOGGING — Auditoría y Seguridad
# ═══════════════════════════════════════════════════════════
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'WARNING',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 10_485_760,       # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'audit.log',
            'maxBytes': 10_485_760,       # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
