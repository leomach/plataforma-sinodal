# Railway optimized settings
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-2q7jnn0^20c8^ui4k1hwjhfq2+h@5)2k#s4^)aai=cduthvt_&')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://app.sinodalgaranhuns.com.br',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
    'https://*.lhr.life',
    'https://*.serveo.net',
]

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'cloudinary_storage',
    'cloudinary',
    'django_htmx',
    'anymail',
    'apps.eventos',
    'apps.usuarios',
    'apps.hub',
    'apps.sessoes',
    'apps.emblemas',
    'apps.pagamentos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
                'apps.emblemas.context_processors.emblemas_pendentes',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'plataforma_db')}",
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Railway/Production Security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Logging — garante que falhas de envio de e-mail (e outros erros das apps)
# apareçam no stdout capturado pela Railway.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cloudinary Configuration
CLOUDINARY_STORAGE = {}
if os.getenv('CLOUDINARY_CLOUD_NAME'):
    CLOUDINARY_STORAGE['CLOUD_NAME'] = os.getenv('CLOUDINARY_CLOUD_NAME')
if os.getenv('CLOUDINARY_API_KEY'):
    CLOUDINARY_STORAGE['API_KEY'] = os.getenv('CLOUDINARY_API_KEY')
if os.getenv('CLOUDINARY_API_SECRET'):
    CLOUDINARY_STORAGE['API_SECRET'] = os.getenv('CLOUDINARY_API_SECRET')
if os.getenv('CLOUDINARY_URL'):
    CLOUDINARY_STORAGE['CLOUDINARY_URL'] = os.getenv('CLOUDINARY_URL')

STORAGES = {
    "default": { "BACKEND": "django.core.files.storage.FileSystemStorage" },
    "staticfiles": { "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" },
}

# Legacy settings for compatibility with older libraries
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
WHITENOISE_KEEP_ONLY_HASHED_FILES=False
WHITENOISE_MANIFEST_STRICT = False

# Use Cloudinary for Media if configured
if os.getenv('CLOUDINARY_CLOUD_NAME'):
    storage_backend = "cloudinary_storage.storage.MediaCloudinaryStorage"
    STORAGES["default"] = { "BACKEND": storage_backend }
    DEFAULT_FILE_STORAGE = storage_backend

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email
#
# A Railway bloqueia todas as portas SMTP de saída (25/465/587/2525) nos planos
# Free/Trial/Hobby. Por isso o envio é feito via API HTTP (porta 443) do Resend,
# usando django-anymail. Em produção defina:
#   EMAIL_BACKEND=anymail.backends.resend.EmailBackend
#   RESEND_API_KEY=re_xxx
# Em desenvolvimento o padrão continua sendo o console.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@sinodalgaranhuns.com.br')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Credenciais dos provedores suportados pelo Anymail (envio via API HTTP)
ANYMAIL = {
    'RESEND_API_KEY': os.getenv('RESEND_API_KEY', ''),
}

# SMTP legado — só funciona se o provedor liberar a porta (ex.: Railway Pro).
# Mantido para compatibilidade caso EMAIL_BACKEND aponte para o backend SMTP.
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# InfinitePay
INFINITEPAY_HANDLE = os.getenv('INFINITEPAY_HANDLE', '')
INFINITEPAY_WEBHOOK_SECRET = os.getenv('INFINITEPAY_WEBHOOK_SECRET', '')
INFINITEPAY_SANDBOX = os.getenv('INFINITEPAY_SANDBOX', 'False') == 'True'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'usuarios.User'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
