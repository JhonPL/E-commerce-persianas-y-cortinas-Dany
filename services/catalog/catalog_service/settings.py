from pathlib import Path

import environ
import cloudinary


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
    "catalogo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "catalog_service.urls"
WSGI_APPLICATION = "catalog_service.wsgi.application"
ASGI_APPLICATION = "catalog_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("CATALOGO_DB_NAME"),
        "USER": env("CATALOGO_DB_USER"),
        "PASSWORD": env("CATALOGO_DB_PASSWORD"),
        "HOST": env("CATALOGO_DB_HOST"),
        "PORT": env("CATALOGO_DB_PORT", default="5432"),
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
        "catalogo.authentication.CatalogServiceTokenAuthentication",
        "catalogo.authentication.RemoteUserAuthentication",
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
    "TITLE": "Catalog Service API",
    "DESCRIPTION": "API independiente para productos, categorías e imágenes.",
    "VERSION": "1.0.0",
}

AUTH_SERVICE_URL = env("AUTH_SERVICE_URL")
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
SERVICE_TIMEOUT_SECONDS = env.int("SERVICE_TIMEOUT_SECONDS", default=5)

CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET", default="")
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)
