from config.settings.base import *

DEBUG = True
ALLOWED_HOSTS = [
    "teamnotfound.duckdns.org"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

CSRF_FAILURE_VIEW = 'django.views.debug.technical_500_response'