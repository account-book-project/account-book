
from .base import *
print(f"[settings prod] DEBUG={DEBUG}  ALLOWED_HOSTS={ALLOWED_HOSTS}")

DEBUG = False
ALLOWED_HOSTS = ["teamnotfound.duckdns.org"]

STATIC_ROOT = BASE_DIR / "staticfiles"

CSRF_TRUSTED_ORIGINS = ["https://teamnotfound.duckdns.org"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
