"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# 프로덕션 설정 모듈 지정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

# WSGI 애플리케이션 가져오기
application = get_wsgi_application()

# BASE_DIR 계산 (settings와 동일한 기준)
BASE_DIR = Path(__file__).resolve().parent.parent

# staticfiles 디렉토리를 WhiteNoise로 서빙
application = WhiteNoise(
    application, root=str(BASE_DIR / "staticfiles"), prefix="static/"
)
