from django.urls import path

from . import oauth_views

app_name = 'oauth'

urlpatterns = [
    # naver
    path(
        'naver/login/', oauth_views.NaverLoginRedirectView.as_view(), name='naver_login'
    ),
    path('naver/callback/', oauth_views.naver_callback, name='naver_callback'),
    # github
    path(
        'github/login/',
        oauth_views.GithubLoginRedirectView.as_view(),
        name='github_login',
    ),
    path('github/callback/', oauth_views.github_callback, name='github_callback'),
    # nickname
    path('check-nickname/', oauth_views.check_nickname_post, name='check_nickname'),
    path('nickname/check/', oauth_views.check_nickname_get, name='check_nickname'),
    path('nickname/', oauth_views.oauth_nickname, name='nickname'),
    # kakaotalk
    path('kakao/login/', oauth_views.KakaoLoginRedirectView.as_view()),
    path('kakao/callback/', oauth_views.kakao_callback),
]
