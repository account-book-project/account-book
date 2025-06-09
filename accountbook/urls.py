# accountbook/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import MyTokenObtainPairSerializer
from .views import (
    AccountListCreateView,
    ActivateUserView,
    CookieTokenObtainPairView,
    LogoutView,
    SignupView,
    TransactionListCreateView,
    UserProfileView,
)


# 커스텀 TokenObtainPairView 정의
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


app_name = 'accountbook'

urlpatterns = [
    # 인증 관련 URL
    path('signup/', SignupView.as_view(), name='signup'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Email 인증
    path(
        'users/activate/<uidb64>/<token>/', ActivateUserView.as_view(), name='activate'
    ),
    # 쿠키 기반 로그인
    path(
        'login/', CookieTokenObtainPairView.as_view(), name='cookie_token_obtain_pair'
    ),
    #  로그아웃 (Refresh Token 블랙리스트 등록)
    path('logout/', LogoutView.as_view(), name='logout'),
    # 사용자 관련 URL
    path('users/me/', UserProfileView.as_view(), name='user_profile'),
    # 계좌 관련 URL
    path('accounts/', AccountListCreateView.as_view(), name='account_list_create'),
    path(
        'accounts/<int:account_id>/transactions/',
        TransactionListCreateView.as_view(),
        name='transaction_list_create',
    ),
]
