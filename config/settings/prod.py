# prod.py
from config.settings.base import *

DEBUG = True
ALLOWED_HOSTS = ['*']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# DATABASES는 base.py 기준 (하드코딩)

