from config.settings.base import *

DEBUG = False
ALLOWED_HOSTS = [
    "teamnotfound.duckdns.org",
    "localhost",
    "127.0.0.1",
    "nginx",
    "my-django",
]

print(f"[settings prod] DEBUG={DEBUG}  ALLOWED_HOSTS={ALLOWED_HOSTS}")

STATIC_ROOT = BASE_DIR / "staticfiles"

# CSRF 설정
CSRF_TRUSTED_ORIGINS = ["https://teamnotfound.duckdns.org"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
