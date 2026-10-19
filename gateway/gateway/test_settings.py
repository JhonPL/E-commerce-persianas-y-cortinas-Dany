import os


os.environ.setdefault("DJANGO_SECRET_KEY", "gateway-tests-only")
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "gateway-internal-test-token")

from .settings import *  # noqa: E402,F403

DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
