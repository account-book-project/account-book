# dev.py
from .base import *

# SECRET_KEY 설정
SECRET_KEY = os.getenv("SECRET_KEY")


# print(f"[DEBUG] SECRET_KEY: {SECRET_KEY}")  # debugging


DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}
