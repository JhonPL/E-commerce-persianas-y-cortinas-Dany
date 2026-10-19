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
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_spectacular",
    "facturacion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "billing_service.urls"
WSGI_APPLICATION = "billing_service.wsgi.application"
ASGI_APPLICATION = "billing_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("BILLING_DB_NAME"),
        "USER": env("BILLING_DB_USER"),
        "PASSWORD": env("BILLING_DB_PASSWORD"),
        "HOST": env("BILLING_DB_HOST"),
        "PORT": env("BILLING_DB_PORT", default="5432"),
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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "facturacion.authentication.InternalServiceTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Billing Service API",
    "DESCRIPTION": "Servicio interno de persistencia de facturas.",
    "VERSION": "1.0.0",
}

INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
