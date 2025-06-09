import json
import os
from datetime import timedelta
from pathlib import Path

# 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# secret.json 읽기
with open(os.path.join(BASE_DIR, 'config', 'secret.json')) as f:
    secrets = json.load(f)


# 🔥 get_secret 함수 정의
def get_secret(setting):
    try:
        return secrets[setting]
    except KeyError:
        raise Exception(f"Set the {setting} setting in secret.json")


# 보안 키
SECRET_KEY = "django-insecure-개발용-secret-key"  # 하드코딩

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
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
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
        "NAME": "django-postgres",
        "USER": "postgres",
        "PASSWORD": "qwe123",  # Docker Compose와 맞추기
        "HOST": "my-db",
        "PORT": "5432",
    }
}

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
    'TITLE': '가계부 API',
    'DESCRIPTION': 'Django REST Framework 기반 가계부 API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'SERVE_PERMISSIONS': [
        'rest_framework.permissions.AllowAny'
    ],  #  Swagger 접근 허용 / # 배포시 삭제하거나 관리자만 Swagger 접속변경필요
}


# 환경변수로 개발/운영 구분
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')  # 기본값: 개발

if DJANGO_ENV == 'production':
    COOKIE_SECURE = True
else:
    COOKIE_SECURE = False

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
else:
    # 개발환경 세팅
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
    ]

    # 로컬에서는 Secure 강제하지 않음
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

# Email 인증
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = get_secret('EMAIL_PORT')
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = get_secret('EMAIL_USE_TLS')
EMAIL_USE_SSL = get_secret('EMAIL_USE_SSL')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
