# dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "django-postgres",
        "USER": "postgres",
        "PASSWORD": "qwe123",
        "HOST": "localhost",  # 로컬 개발 환경에서는 localhost로 변경
        "PORT": "5432",
    }
}
