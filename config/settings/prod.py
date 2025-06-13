from config.settings.base import *

DEBUG = False  # 운영처럼!
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1"]  # 로컬/모든 접속 허용
STATIC_ROOT = BASE_DIR / "staticfiles"
