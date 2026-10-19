from datetime import timedelta
from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "usuarios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "auth_service.urls"
WSGI_APPLICATION = "auth_service.wsgi.application"
ASGI_APPLICATION = "auth_service.asgi.application"
AUTH_USER_MODEL = "usuarios.Usuario"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("IDENTITY_DB_NAME"),
        "USER": env("IDENTITY_DB_USER"),
        "PASSWORD": env("IDENTITY_DB_PASSWORD"),
        "HOST": env("IDENTITY_DB_HOST"),
        "PORT": env("IDENTITY_DB_PORT", default="5432"),
        "OPTIONS": {
            "options": "-c timezone=America/Bogota",
        },
    }
}

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
STATIC_URL = "static/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "usuarios.authentication.InternalServiceTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "usuario_id",
    "USER_ID_CLAIM": "usuario_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Identity Service API",
    "DESCRIPTION": "Servicio de identidad, perfiles y administración de usuarios.",
    "VERSION": "1.0.0",
}

INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_CLIENT_ID", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS = env.list(
    "GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS",
    default=["http://localhost:5173/oauth/google"],
)
