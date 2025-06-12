from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookie(response, user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # 액세스 토큰: 1시간
    response.set_cookie(
        key='access',
        value=access_token,
        max_age=60 * 60,  # 1시간
        httponly=True,
        secure=True,  # dev 환경에선 False
        samesite='Lax',
        path='/',
    )

    # 리프레시 토큰: 7일
    response.set_cookie(
        key='refresh',
        value=str(refresh),
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=True,
        samesite='Lax',
        path='/',
    )
    return response
