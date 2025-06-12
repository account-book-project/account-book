from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('admin/', admin.site.urls),
    # 임시 메인
    path('', TemplateView.as_view(template_name="main.html"), name='main'),
    # API 엔드포인트
    path('api/auth/', include('accountbook.urls.auth_urls')),
    path('api/users/', include('accountbook.urls.user_urls')),
    path('api/accounts/', include('accountbook.urls.account_urls')),
    path('api/', include('accountbook.urls.transaction_urls')),
    # API 문서 (항상 접근 가능)
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name='schema',
    ),
    path(
        'swagger/',
        SpectacularSwaggerView.as_view(
            url_name='schema', permission_classes=[AllowAny]
        ),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny]),
        name='redoc',
    ),
    # include
    path('oauth/', include('oauth.oauth_urls')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
