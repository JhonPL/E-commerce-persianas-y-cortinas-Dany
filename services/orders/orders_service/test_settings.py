import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-for-deployment")
os.environ.setdefault("ORDERS_DB_NAME", "unused")
os.environ.setdefault("ORDERS_DB_USER", "unused")
os.environ.setdefault("ORDERS_DB_PASSWORD", "unused")
os.environ.setdefault("ORDERS_DB_HOST", "localhost")
os.environ.setdefault(
    "AUTH_SERVICE_URL",
    "http://localhost:8004/api/v1/auth/me/",
)
os.environ.setdefault(
    "CATALOGO_SERVICE_INTERNAL_URL",
    "http://localhost:8001/api/internal/catalogo",
)
os.environ.setdefault("CART_SERVICE_URL", "http://localhost:8002/api/v1/carrito")

from .settings import *  # noqa: E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
