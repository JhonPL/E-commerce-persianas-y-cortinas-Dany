from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["ucc.bluelineroofingconstruction.com"])
CORS_ALLOWED_ORIGINS = env.list(
	"CORS_ALLOWED_ORIGINS",
	default=["https://ucc.bluelineroofingconstruction.com"],
)
CSRF_TRUSTED_ORIGINS = env.list(
	"CSRF_TRUSTED_ORIGINS",
	default=["https://ucc.bluelineroofingconstruction.com"],
)
GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS = env.list(
	"GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS",
	default=["https://ucc.bluelineroofingconstruction.com/oauth/google"],
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True