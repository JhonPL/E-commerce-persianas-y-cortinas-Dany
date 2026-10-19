import os

os.environ.setdefault(
    "DJANGO_SECRET_KEY",
    "test-only-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault("BILLING_DB_NAME", "unused")
os.environ.setdefault("BILLING_DB_USER", "unused")
os.environ.setdefault("BILLING_DB_PASSWORD", "unused")
os.environ.setdefault("BILLING_DB_HOST", "localhost")

from .settings import *  # noqa: E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
