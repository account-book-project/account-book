from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accountbook.serializers import MyTokenObtainPairSerializer
from accountbook.views.auth_views import (
    ActivateUserView,
    CookieTokenObtainPairView,
    LogoutView,
    SignupView,
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CookieTokenObtainPairView.as_view(), name='cookie_login'),
    path(
        'login/', CookieTokenObtainPairView.as_view(), name='cookie_token_obtain_pair'
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('activate/<uidb64>/<token>/', ActivateUserView.as_view(), name='activate'),
]
