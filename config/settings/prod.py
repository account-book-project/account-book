from config.settings.base import *

DEBUG = False
ALLOWED_HOSTS = [
    "teamnotfound.duckdns.org"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

CSRF_TRUSTED_ORIGINS = [
    "https://teamnotfound.duckdns.org"
]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
