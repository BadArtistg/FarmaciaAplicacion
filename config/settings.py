import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env si existe
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-farmacia-inacap-temuco-sprint1-key-2026-production-ready'
)

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',') if host.strip()
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 2FA / TOTP
    'django_otp',
    'django_otp.plugins.otp_totp',

    # Módulos del Sistema Web Farmacia Mixta
    'apps.seguridad.apps.SeguridadConfig',
    'apps.inventario.apps.InventarioConfig',
    'apps.recetas.apps.RecetasConfig',
    'apps.dispensacion.apps.DispensacionConfig',
    'apps.caja.apps.CajaConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.seguridad.middleware.SeguridadHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.seguridad.context_processors.auth_roles',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de datos
USE_POSTGRES = os.getenv('USE_POSTGRES', 'False').lower() in ('true', '1', 't')

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'farmacia_db'),
            'USER': os.getenv('DB_USER', 'farmacia_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'farmacia_pass'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Modelo de Usuario personalizado (Crucial desde Sprint 1)
AUTH_USER_MODEL = 'seguridad.Usuario'

# Password validation - Mínimo 10 caracteres conforme al informe (Sec. 6.2)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internacionalización
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos y media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad de Sesiones y Cookies (OWASP)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 14400  # 4 horas
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

LOGIN_URL = 'seguridad:login'
LOGIN_REDIRECT_URL = 'inventario:dashboard'
LOGOUT_REDIRECT_URL = 'seguridad:login'

# Modo práctica para simulación estudiantil en INACAP
MODO_PRACTICA = os.getenv('MODO_PRACTICA', 'True').lower() in ('true', '1', 't')
CODIGO_2FA_PRACTICA = '123456'
MAX_INTENTOS_LOGIN = 5
