import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-for-deployment")
os.environ.setdefault("CATALOGO_DB_NAME", "unused")
os.environ.setdefault("CATALOGO_DB_USER", "unused")
os.environ.setdefault("CATALOGO_DB_PASSWORD", "unused")
os.environ.setdefault("CATALOGO_DB_HOST", "localhost")
os.environ.setdefault(
    "AUTH_SERVICE_URL",
    "http://localhost:8004/api/v1/auth/me/",
)

from .settings import *  # noqa: E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
