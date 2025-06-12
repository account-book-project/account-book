from urllib.parse import parse_qs, urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.base_user import BaseUserManager
from django.core import signing
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accountbook.utils.jwt_cookie import set_jwt_cookie
from oauth.serializers import (  # 👈 반드시 serializers 위치 확인
    NicknameCheckSerializer,
    NicknameSerializer,
)

User = get_user_model()


#  OAuth 기본 상수
NAVER_CALLBACK_URL = '/oauth/naver/callback/'
NAVER_STATE = 'naver_login'
NAVER_LOGIN_URL = 'https://nid.naver.com/oauth2.0/authorize'
NAVER_TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
NAVER_PROFILE_URL = 'https://openapi.naver.com/v1/nid/me'

GITHUB_CALLBACK_URL = '/oauth/github/callback/'
GITHUB_STATE = 'github_login'
GITHUB_LOGIN_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_PROFILE_URL = 'https://api.github.com/user'

KAKAO_LOGIN_URL = 'https://kauth.kakao.com/oauth/authorize'
KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_PROFILE_URL = 'https://kapi.kakao.com/v2/user/me'
KAKAO_CALLBACK_URL = '/oauth/kakao/callback/'


#  NAVER 로그인 Redirect
class NaverLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        domain = self.request.scheme + '://' + self.request.META.get('HTTP_HOST', '')
        callback_url = domain + NAVER_CALLBACK_URL
        state = signing.dumps(NAVER_STATE)

        params = {
            'response_type': 'code',
            'client_id': settings.NAVER_CLIENT_ID,
            'redirect_uri': callback_url,
            'state': state,
        }

        return f'{NAVER_LOGIN_URL}?{urlencode(params)}'


#  NAVER Callback 처리
def naver_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    if NAVER_STATE != signing.loads(state):
        raise Http404("Invalid state value")

    access_token = get_naver_access_token(code, state)
    profile = get_naver_profile(access_token)
    email = profile.get('email')

    user = User.objects.filter(email=email).first()
    if user:
        if not user.is_active:
            user.is_active = True
            user.save()
        login(request, user)
        return redirect('main')

    return redirect(
        reverse('oauth:nickname') + f'?access_token={access_token}&oauth=naver'
    )


# GitHub 로그인 Redirect
class GithubLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        domain = self.request.scheme + '://' + self.request.META.get('HTTP_HOST', '')
        callback_url = domain + GITHUB_CALLBACK_URL
        state = signing.dumps(GITHUB_STATE)

        params = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'redirect_uri': callback_url,
            'state': state,
        }

        return f'{GITHUB_LOGIN_URL}?{urlencode(params)}'


#  GitHub Callback 처리
def github_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    if GITHUB_STATE != signing.loads(state):
        raise Http404("Invalid state value")

    access_token = get_github_access_token(code, state)
    if not access_token:
        raise Http404("Access token 없음")

    profile = get_github_profile(access_token)
    email = profile.get('email')

    user = User.objects.filter(email=email).first()
    if user:
        if not user.is_active:
            user.is_active = True
            user.save()
        login(request, user)
        return redirect('main')

    return redirect(
        reverse('oauth:nickname') + f'?access_token={access_token}&oauth=github'
    )


#  닉네임 설정 (회원가입 최종 단계)
@extend_schema(
    parameters=[
        OpenApiParameter(
            "access_token",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="네이버/깃허브 access_token",
        ),
        OpenApiParameter(
            "oauth",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="naver 또는 github",
        ),
    ],
    request=NicknameSerializer,
    responses={201: None},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def oauth_nickname(request):
    access_token = request.query_params.get('access_token')
    oauth = request.query_params.get('oauth')

    if not access_token or oauth not in ['naver', 'github']:
        return Response(
            {'detail': '잘못된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = NicknameSerializer(data=request.data)
    if serializer.is_valid():
        nickname = serializer.validated_data['nickname']

        if oauth == 'naver':
            profile = get_naver_profile(access_token)
        else:
            profile = get_github_profile(access_token)

        email = profile.get('email')
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': '이미 가입된 이메일입니다.'}, status=status.HTTP_409_CONFLICT
            )

        user = User(email=email, nickname=nickname, is_active=True)
        user.set_password(get_random_string(12))
        user.save()

        login(request, user)

        response = Response(
            {'detail': '회원가입 및 로그인 성공'}, status=status.HTTP_201_CREATED
        )
        return set_jwt_cookie(response, user)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#  NAVER 액세스 토큰 요청
def get_naver_access_token(code, state):
    params = {
        'grant_type': 'authorization_code',
        'client_id': settings.NAVER_CLIENT_ID,
        'client_secret': settings.NAVER_SECRET,
        'code': code,
        'state': state,
    }

    response = requests.get(NAVER_TOKEN_URL, params=params)
    if response.status_code != 200:
        raise Http404("NAVER 토큰 요청 실패")

    return response.json().get('access_token')


#  NAVER 프로필 요청
def get_naver_profile(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(NAVER_PROFILE_URL, headers=headers)
    if response.status_code != 200:
        raise Http404("NAVER 프로필 요청 실패")

    return response.json().get('response')


#  GitHub 액세스 토큰 요청
def get_github_access_token(code, state):
    params = {
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_SECRET,
        'code': code,
        'state': state,
    }

    response = requests.get(GITHUB_TOKEN_URL, params=params)
    if response.status_code != 200:
        return None

    parsed = parse_qs(response.content.decode())
    return parsed.get('access_token', [None])[0]


#  GitHub 프로필 요청
def get_github_profile(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    print("== get_github_profile ==")
    print(f"access_token: {access_token}")
    print(f"headers: {headers}")

    response = requests.get(GITHUB_PROFILE_URL, headers=headers)
    print(f"response.status_code: {response.status_code}")
    print(f"response.text: {response.text}")

    if response.status_code != 200:
        raise Http404("GitHub 프로필 요청 실패")

    result = response.json()
    if not result.get('email'):
        result['email'] = f'{result["login"]}@id.github.com'
    return result


#  닉네임 중복 확인
@extend_schema(
    parameters=[
        OpenApiParameter(
            name="nickname",
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="중복 확인할 닉네임",
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="사용 가능 여부 응답",
            examples=[
                {"name": "사용 가능", "value": {"is_available": True}},
                {
                    "name": "사용 불가",
                    "value": {
                        "is_available": False,
                        "detail": "이미 사용 중인 닉네임입니다.",
                    },
                },
            ],
        )
    },
    summary="닉네임 중복 확인 (GET)",
    description="닉네임이 사용 가능한지 GET 요청으로 확인합니다.",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_nickname_get(request):
    serializer = NicknameCheckSerializer(data=request.query_params)
    if serializer.is_valid():
        return Response({'is_available': True}, status=status.HTTP_200_OK)
    return Response(
        {
            'is_available': False,
            'detail': serializer.errors.get('nickname', ['유효하지 않은 요청입니다.'])[
                0
            ],
        },
        status=status.HTTP_200_OK,
    )


# 닉네임 중복 확인 swagger용


@extend_schema(
    request=NicknameCheckSerializer,
    responses={200: None},
    summary="닉네임 중복 확인 (POST)",
    description="닉네임이 사용 가능한지 POST 요청으로 확인합니다.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def check_nickname_post(request):
    serializer = NicknameCheckSerializer(data=request.data)
    if serializer.is_valid():
        return Response({"available": True}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# KAKAO 로그인 Redirect
class KakaoLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        params = {
            'client_id': settings.KAKAO_CLIENT_ID,
            'redirect_uri': settings.KAKAO_REDIRECT_URI,
            'response_type': 'code',
        }
        url = "https://kauth.kakao.com/oauth/authorize?" + urlencode(params)
        return url


def kakao_callback(request):
    code = request.GET.get('code')
    # 1. 액세스 토큰 요청
    token_json = get_kakao_access_token(
        code,
        redirect_uri='http://localhost:8000/oauth/kakao/callback/',
        client_id=settings.KAKAO_CLIENT_ID,
        client_secret=getattr(settings, 'KAKAO_CLIENT_SECRET', None),
    )
    access_token = token_json.get('access_token')
    if not access_token:
        return HttpResponse("토큰 발급 실패!")

    # 2. 사용자 정보 요청
    profile = get_kakao_profile(access_token)
    kakao_id = profile.get('id')
    kakao_account = profile.get('kakao_account', {})
    kakao_email = kakao_account.get('email')
    nickname = profile.get('properties', {}).get('nickname', f'kakao_{kakao_id}')

    # 이메일 없을 경우, 대체 이메일 생성
    if not kakao_email:
        kakao_email = f"{kakao_id}@kakao.com"

    # 3. 사용자 등록/로그인 (이메일 or id 기준)
    user, created = User.objects.get_or_create(
        email=kakao_email,
        defaults={
            'nickname': nickname,
            'is_active': True,
        },
    )

    login(request, user)

    # 4. JWT 쿠키 발급 (필요하다면 set_jwt_cookie 사용)
    response = redirect('main')  # 배포시 ('https://mydomain.com/oauth/success')
    return set_jwt_cookie(response, user)


# 카카오 엑세스 토큰 발급
def get_kakao_access_token(code, redirect_uri, client_id, client_secret=None):
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code,
    }
    if client_secret:
        data['client_secret'] = client_secret

    response = requests.post(url, data=data)
    return response.json()


# 카카오 유저 조희
def get_kakao_profile(access_token):
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()
