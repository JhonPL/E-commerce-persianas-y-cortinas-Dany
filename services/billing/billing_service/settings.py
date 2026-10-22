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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    },
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
INVOICE_ISSUER_ADDRESS = env("INVOICE_ISSUER_ADDRESS", default="") or (
    "Cra. 13 # 20 - 52, Granada, Meta"
)
INVOICE_ISSUER_PHONE = env("INVOICE_ISSUER_PHONE", default="") or "312 355 8218"
INVOICE_ISSUER_EMAIL = env("INVOICE_ISSUER_EMAIL", default="") or (
    "percortinasdany@gmail.com"
)
INVOICE_ISSUER_NIT = env("INVOICE_ISSUER_NIT", default="") or "1.122.507.213-3"
INVOICE_ISSUER_WEBSITE = env(
    "INVOICE_ISSUER_WEBSITE",
    default="",
)
