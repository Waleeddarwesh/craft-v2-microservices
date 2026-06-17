import os
import sys
from pathlib import Path
import environ
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Add craft-common to path for local dev if not installed
sys.path.insert(0, str(BASE_DIR.parent.parent / 'shared' / 'craft-common'))

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

ENVIRONMENT = env('ENVIRONMENT', default='development')
SECRET_KEY = env('SECRET_KEY', default='django-insecure-auth-service')
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:3000'])

INSTALLED_APPS = [
    'django_prometheus',
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'social_django',
    'drf_yasg',
    
    # Local
    'accounts',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'craft_common.middleware.request_id.RequestIDMiddleware',
    'craft_common.middleware.fix_host.BypassHostCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'auth_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auth_service.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/auth_db')
}
# Set search path to auth_service schema
DATABASES['default']['OPTIONS'] = {'options': '-c search_path=auth_service,public'}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

RABBITMQ_URL = env('RABBITMQ_URL', default='amqp://guest:guest@localhost:5672/')

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

from craft_common.auth.jwt_keys import get_or_create_jwt_keys

if ENVIRONMENT == 'development':
    private_key_content, public_key_content = get_or_create_jwt_keys(BASE_DIR)

if ENVIRONMENT != 'development':
    private_key_env = env('JWT_PRIVATE_KEY', default='')
    public_key_env = env('JWT_PUBLIC_KEY', default='')
    if not private_key_env or not public_key_env:
        raise ImproperlyConfigured("JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be set in production.")
    private_key_content = private_key_env
    public_key_content = public_key_env

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': private_key_content,
    'VERIFYING_KEY': public_key_content,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'craft_common.logging.structured_logger.RequestIDFilter',
        },
    },
    'formatters': {
        'json': {
            '()': 'craft_common.logging.structured_logger.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# OpenTelemetry settings
import os
OTEL_SERVICE_NAME = os.environ.get('OTEL_SERVICE_NAME', 'auth-service')

import django.http.request
django.http.request.host_validation_re = __import__('re').compile(r'^[a-zA-Z0-9_.-]+$')


import django.http.request
django.http.request.host_validation_re = __import__('re').compile(r'^[a-zA-Z0-9_.-]+$')


# Enable django-prometheus DB metrics
if 'default' in DATABASES:
    DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.postgresql'
