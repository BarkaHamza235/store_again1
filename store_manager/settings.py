from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Assure l'existence du répertoire des logs
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SECRET_KEY = 'django-insecure-your-secret-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = []

# Applications du projet
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tiers
    'crispy_forms',
    'crispy_bootstrap5',

    # Projet
    'apps.accounts.apps.AccountsConfig',
    'apps.core',
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

ROOT_URLCONF = 'store_manager.urls'

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
                'django.template.context_processors.media',  # Ajouté pour MEDIA_URL
            ],
        },
    },
]

WSGI_APPLICATION = 'store_manager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 5,
            'init_command': """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA mmap_size=134217728;
                PRAGMA journal_size_limit=67108864;
                PRAGMA cache_size=2000;
            """,
            'transaction_mode': 'IMMEDIATE',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth utilisateur personnalisé
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs avec namespaces corrects
LOGIN_URL = 'accounts:login'             # /accounts/login/
LOGIN_REDIRECT_URL = 'core:home'         # /core/home/
LOGOUT_REDIRECT_URL = 'accounts:login'   # /accounts/login/

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuration EMAIL pour développement (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Pour production avec Gmail, décommentez et configurez:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'barkahamza454@gmail.com'
EMAIL_HOST_PASSWORD = 'ptam jrxs dfvc nahw'
DEFAULT_FROM_EMAIL = 'Store Manager <barkahamza454@gmail.com>'

# Messages framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR / 'logs/app.log'),
            'maxBytes': 2621440,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}
