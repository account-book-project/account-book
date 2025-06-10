from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # 기능별 URL 모듈 분리
    path('api/auth/', include('accountbook.urls.auth_urls')),
    path('api/users/', include('accountbook.urls.user_urls')),
    path('api/accounts/', include('accountbook.urls.account_urls')),
    path('api/', include('accountbook.urls.transaction_urls')),  # 거래는 계좌 경로 포함
    # API 문서
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'
    ),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 개발환경에서만 정적/미디어 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
