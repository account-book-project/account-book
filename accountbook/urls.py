from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, UserProfileView, AccountListCreateView, TransactionListCreateView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# 커스텀 TokenObtainPairView 정의
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

app_name = 'accountbook'

urlpatterns = [
    # 인증 관련 URL
    path('signup/', SignupView.as_view(), name='signup'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 사용자 관련 URL
    path('users/me/', UserProfileView.as_view(), name='user_profile'),

    # 계좌 관련 URL
    path('accounts/', AccountListCreateView.as_view(), name='account_list_create'),
    path('accounts/<int:account_id>/transactions/', TransactionListCreateView.as_view(),
         name='transaction_list_create'),
]
