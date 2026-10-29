import environ
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# The shared container entrypoint runs migrate; this gateway has no owned data.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "gateway.urls"
WSGI_APPLICATION = "gateway.wsgi.application"
ASGI_APPLICATION = "gateway.asgi.application"

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)
CORS_ALLOW_CREDENTIALS = True

IDENTITY_SERVICE_URL = env(
    "IDENTITY_SERVICE_URL",
    default="http://127.0.0.1:8004",
).rstrip("/")
CATALOGO_SERVICE_URL = env(
    "CATALOGO_SERVICE_URL",
    default="http://127.0.0.1:8001/api/v1/catalogo",
).rstrip("/")
CATALOGO_SERVICE_INTERNAL_URL = env(
    "CATALOGO_SERVICE_INTERNAL_URL",
    default="http://127.0.0.1:8001/api/internal/catalogo",
).rstrip("/")
CART_SERVICE_URL = env(
    "CART_SERVICE_URL",
    default="http://127.0.0.1:8002/api/v1/carrito",
).rstrip("/")
CART_SERVICE_INTERNAL_URL = env(
    "CART_SERVICE_INTERNAL_URL",
    default="http://127.0.0.1:8002/api/internal/carrito",
).rstrip("/")
ORDERS_SERVICE_URL = env(
    "ORDERS_SERVICE_URL",
    default="http://127.0.0.1:8003",
).rstrip("/")
ORDERS_SERVICE_TIMEOUT_SECONDS = env.int(
    "ORDERS_SERVICE_TIMEOUT_SECONDS",
    default=30,
)
PAYMENTS_SERVICE_URL = env(
    "PAYMENTS_SERVICE_URL",
    default="http://127.0.0.1:8007/api/v1/payments",
).rstrip("/")
NOTIFICATIONS_SERVICE_URL = env(
    "NOTIFICATIONS_SERVICE_URL",
    default="http://127.0.0.1:8005",
).rstrip("/")
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")
SERVICE_TIMEOUT_SECONDS = env.int("SERVICE_TIMEOUT_SECONDS", default=5)
PAYMENTS_SERVICE_TIMEOUT_SECONDS = env.int(
    "PAYMENTS_SERVICE_TIMEOUT_SECONDS",
    default=60,
)

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True