from config.settings.base import *

DEBUG = True
ALLOWED_HOSTS = [
    "teamnotfound.duckdns.org"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

CSRF_FAILURE_VIEW = 'django.views.debug.technical_500_response'

CSRF_TRUSTED_ORIGINS = ["https://teamnotfound.duckdns.org"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")