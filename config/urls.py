from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# drf-spectacular
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI (API 문서)
    path(
        'swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'
    ),
    # ReDoc (API 문서 다른 스타일)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # AccountBook 앱 API 엔드포인트
    path('api/', include('accountbook.urls')),
]

# 개발환경용 Static, Media 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
