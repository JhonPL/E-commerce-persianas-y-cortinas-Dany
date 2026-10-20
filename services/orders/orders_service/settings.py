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
    "pedidos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "orders_service.urls"
WSGI_APPLICATION = "orders_service.wsgi.application"
ASGI_APPLICATION = "orders_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("ORDERS_DB_NAME"),
        "USER": env("ORDERS_DB_USER"),
        "PASSWORD": env("ORDERS_DB_PASSWORD"),
        "HOST": env("ORDERS_DB_HOST"),
        "PORT": env("ORDERS_DB_PORT", default="5432"),
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
        "pedidos.authentication.InternalServiceTokenAuthentication",
        "pedidos.authentication.RemoteUserAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Orders Service API",
    "DESCRIPTION": "API independiente de pedidos y direcciones de entrega.",
    "VERSION": "1.0.0",
}

AUTH_SERVICE_URL = env("AUTH_SERVICE_URL")
CATALOGO_SERVICE_INTERNAL_URL = env("CATALOGO_SERVICE_INTERNAL_URL")
CART_SERVICE_URL = env("CART_SERVICE_URL")
NOTIFICATIONS_SERVICE_URL = env(
    "NOTIFICATIONS_SERVICE_URL",
    default="http://127.0.0.1:8005",
).rstrip("/")
SERVICE_TIMEOUT_SECONDS = env.int("SERVICE_TIMEOUT_SECONDS", default=5)
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
