import json
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent


dotenv_files = [BASE_DIR / '.env.local', BASE_DIR / '.env']
for dotenv_path in dotenv_files:
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)

# 2. 환경변수로부터 값 불러오기
SECRET_KEY = os.getenv('SECRET_KEY')
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'false') == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false') == 'true'


# 기본 디버그
DEBUG = True  # dev.py, prod.py에서 따로 override

ALLOWED_HOSTS = ["*"]  # Docker 외부 접속

# 앱 등록
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accountbook",
    "core",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "debug_toolbar",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # <-- 여기!
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}
# 분기 설정 for redis
REDIS_HOST = "127.0.0.1"
if os.getenv("DJANGO_ENV") == "production":
    REDIS_HOST = "my-redis"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# 디버그 툴바가 로컬에서만 보이도록 설정
INTERNAL_IPS = [
    '127.0.0.1',  # 기본 로컬호스트
]

# 비밀번호 검증
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# 국제화
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static 파일
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 기본 primary key type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 유저 인증
AUTH_USER_MODEL = 'accountbook.CustomUser'

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accountbook.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',  #  Pagination 추가
    'PAGE_SIZE': 10,  # Pagination 추가
}

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'TOKEN_OBTAIN_SERIALIZER': 'accountbook.serializers.MyTokenObtainPairSerializer',
}

# drf-spectacular 설정
SPECTACULAR_SETTINGS = {
    "TITLE": "가계부 API",
    "DESCRIPTION": "Django REST Framework 기반 가계부 API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SECURITY": [{"bearerAuth": []}],  # 권한설정
    "COMPONENTS": {
        "securitySchemes": {  # 권한설정
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}


# 환경변수로 개발/운영 구분
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    BASE_URL = "https://yourdomain.com"  # 운영 서버 주소로!
else:
    BASE_URL = "http://localhost:8000"  # 개발 환경

# CORS 설정
CORS_ALLOW_CREDENTIALS = True

if DJANGO_ENV == 'production':
    # 운영환경 세팅
    CORS_ALLOWED_ORIGINS = [
        "https://yourfrontenddomain.com",
    ]

    # CSRF / SESSION 쿠키를 HTTPS에서만 주고받게 설정
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    COOKIE_SECURE = True

else:
    # 개발환경 세팅
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
    ]

    # 로컬에서는 Secure 강제하지 않음
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    COOKIE_SECURE = True

# Email 인증
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = get_secret('EMAIL_PORT')
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = get_secret('EMAIL_USE_TLS')
EMAIL_USE_SSL = get_secret('EMAIL_USE_SSL')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
