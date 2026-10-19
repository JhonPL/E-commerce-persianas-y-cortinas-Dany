from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_spectacular",
    "notificaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "notification_service.urls"
WSGI_APPLICATION = "notification_service.wsgi.application"
ASGI_APPLICATION = "notification_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("NOTIFICATIONS_DB_NAME"),
        "USER": env("NOTIFICATIONS_DB_USER"),
        "PASSWORD": env("NOTIFICATIONS_DB_PASSWORD"),
        "HOST": env("NOTIFICATIONS_DB_HOST"),
        "PORT": env("NOTIFICATIONS_DB_PORT", default="5432"),
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
        "notificaciones.authentication.InternalServiceTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Notification Service API",
    "DESCRIPTION": "Servicio de notificaciones y registro de entrega.",
    "VERSION": "1.0.0",
}

INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
ADMIN_EMAIL = env("ADMIN_EMAIL", default="admin@tutienda.com")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
