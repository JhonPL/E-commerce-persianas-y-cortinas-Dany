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
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_spectacular",
    "simulador",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "payments_service.urls"
WSGI_APPLICATION = "payments_service.wsgi.application"
ASGI_APPLICATION = "payments_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("PAYMENTS_DB_NAME"),
        "USER": env("PAYMENTS_DB_USER"),
        "PASSWORD": env("PAYMENTS_DB_PASSWORD"),
        "HOST": env("PAYMENTS_DB_HOST"),
        "PORT": env("PAYMENTS_DB_PORT", default="5432"),
        "OPTIONS": {"options": "-c timezone=America/Bogota"},
    }
}

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "simulador.authentication.RemoteUserAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Simulador de pagos",
    "DESCRIPTION": (
        "Pagos demostrativos. No procesa dinero ni recopila datos de tarjetas."
    ),
    "VERSION": "1.0.0",
}

INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
AUTH_SERVICE_URL = env(
    "AUTH_SERVICE_URL",
    default="http://127.0.0.1:8004/api/v1/auth/me/",
)
ORDERS_SERVICE_URL = env(
    "ORDERS_SERVICE_URL",
    default="http://127.0.0.1:8003",
)
SERVICE_TIMEOUT_SECONDS = env.int("SERVICE_TIMEOUT_SECONDS", default=5)
PAYMENT_SIMULATOR_ENABLED = env.bool("PAYMENT_SIMULATOR_ENABLED", default=False)
PAYMENT_IDEMPOTENCY_WINDOW = timedelta(minutes=15)