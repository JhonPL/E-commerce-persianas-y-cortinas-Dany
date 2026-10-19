import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-for-deployment")
os.environ.setdefault("PAYMENTS_DB_NAME", "unused")
os.environ.setdefault("PAYMENTS_DB_USER", "unused")
os.environ.setdefault("PAYMENTS_DB_PASSWORD", "unused")
os.environ.setdefault("PAYMENTS_DB_HOST", "localhost")

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]