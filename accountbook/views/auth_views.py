# accountbook/views/auth_views.py

import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema
from django.utils import timezone

from ..serializers import SignupSerializer

# 로거 설정
logger = logging.getLogger('accountbook.auth')

User = get_user_model()


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="회원가입",
        description="새로운 사용자를 생성합니다.",
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user_id": {"type": "integer"},
                },
            }
        },
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # IP 기반 회원가입 속도 제한
        ip_address = self._get_client_ip(request)
        cache_key = f'signup_rate_limit_{ip_address}'

        # 10분에 3회로 제한
        signup_attempts = cache.get(cache_key, 0)
        if signup_attempts >= 3:
            logger.warning(f"Signup rate limit exceeded from IP: {ip_address}")
            return Response(
                {"message": "회원가입 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 트랜잭션 내에서 사용자 생성
        try:
            user = serializer.save()

            # 회원가입 시도 횟수 증가
            cache.set(cache_key, signup_attempts + 1, timeout=60 * 10)  # 10분

            # 성공 로깅
            logger.info(f"User created successfully: {user.id} from {ip_address}")

            return Response(
                {"message": "회원가입이 완료되었습니다.", "user_id": user.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            # 실패 로깅
            logger.error(f"User creation failed from {ip_address}: {str(e)}")

            return Response(
                {"message": "회원가입 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CookieTokenObtainPairView(TokenObtainPairView):
    # 로그인: JWT 발급 + 쿠키 저장

    @extend_schema(
        summary="로그인 (JWT 쿠키 저장)",
        description="로그인 후 JWT 토큰을 쿠키에 저장합니다.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            # 로그인 시도 횟수 제한 (브루트포스 공격 방지)
            username = request.data.get('username', '')
            ip_address = self._get_client_ip(request)

            if username:
                # 사용자명 + IP 기반 캐시 키 생성
                cache_key = f'login_attempts_{username}_{ip_address}'
                login_attempts = cache.get(cache_key, 0)

                # 5분 내 5회 이상 실패 시 잠금
                if login_attempts >= 5:
                    logger.warning(f"Login rate limit exceeded: {username} from {ip_address}")
                    return Response(
                        {"message": "너무 많은 로그인 시도. 5분 후에 다시 시도하세요."},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # 로그인 성공 시 시도 횟수 초기화
                if username:
                    cache.delete(cache_key)

                    # 사용자 로그인 시간 업데이트 (선택적)
                    try:
                        user = User.objects.get(username=username)
                        user.last_login = timezone.now()
                        user.save(update_fields=['last_login'])
                    except User.DoesNotExist:
                        pass

                    logger.info(f"User logged in: {username} from {ip_address}")

                refresh_token = response.data.get('refresh')
                access_token = response.data.get('access')

                response.data = {"message": "로그인 성공"}

                cookie_max_age = 60 * 60 * 24 * 7  # 7일

                # 보안 설정 강화
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    max_age=cookie_max_age,
                    httponly=True,
                    secure=settings.COOKIE_SECURE,
                    samesite='Lax',
                    path='/',
                )
                response.set_cookie(
                    key='refresh_token',
                    value=refresh_token,
                    max_age=cookie_max_age,
                    httponly=True,
                    secure=settings.COOKIE_SECURE,
                    samesite='Lax',
                    path='/',
                )
            else:
                # 로그인 실패 시 시도 횟수 증가
                if username:
                    cache.set(cache_key, login_attempts + 1, timeout=60 * 5)  # 5분 유효
                    logger.warning(f"Failed login attempt: {username} from {ip_address}")

            return response
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response(
                {"message": "로그인 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="로그아웃",
        description="JWT 토큰 쿠키 삭제 및 Refresh Token 블랙리스트 등록",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        ip_address = self._get_client_ip(request)

        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if refresh_token:
                # 블랙리스트 등록
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User logged out: {user_id} from {ip_address}")

        except Exception as e:
            # 블랙리스트 등록 실패해도 쿠키 삭제는 계속
            logger.warning(f"Token blacklist failed for user {user_id}: {str(e)}")

        response = Response({"message": "로그아웃 성공"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response

    def _get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# 이메일 인증 처리
class ActivateUserView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request, uidb64, token):
        ip_address = self._get_client_ip(request)

        try:
            # 캐싱을 통한 중복 인증 요청 방지
            cache_key = f'email_activation_{uidb64}_{token}'
            if cache.get(cache_key):
                return Response(
                    {"message": "이미 처리된 인증 요청입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # IP 기반 속도 제한
            ip_cache_key = f'activation_rate_limit_{ip_address}'
            activation_attempts = cache.get(ip_cache_key, 0)

            if activation_attempts >= 10:  # 10분에 10회로 제한
                logger.warning(f"Activation rate limit exceeded from IP: {ip_address}")
                return Response(
                    {"message": "너무 많은 인증 시도. 잠시 후 다시 시도하세요."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # 시도 횟수 증가
            cache.set(ip_cache_key, activation_attempts + 1, timeout=60 * 10)  # 10분

            uid = urlsafe_base64_decode(uidb64).decode()

            # 필요한 필드만 조회
            user = User.objects.filter(pk=uid).only('id', 'is_active', 'email').first()

            if not user:
                logger.warning(f"Invalid activation attempt from {ip_address}: User not found for uid {uid}")
                return Response(
                    {"message": "유효하지 않은 인증 링크입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.is_active:
                logger.info(f"Activation attempt from {ip_address} for already active user: {user.id}")
                return Response(
                    {"message": "이미 인증된 계정입니다."},
                    status=status.HTTP_200_OK,
                )

            if default_token_generator.check_token(user, token):
                # 트랜잭션 내에서 사용자 활성화
                user.is_active = True
                user.save(update_fields=['is_active'])  # 필요한 필드만 업데이트

                # 인증 완료 상태 캐싱 (1시간)
                cache.set(cache_key, True, timeout=60 * 60)

                logger.info(f"User activated successfully from {ip_address}: {user.id} ({user.email})")

                return Response(
                    {"message": "이메일 인증이 완료되었습니다."}, status=status.HTTP_200_OK
                )
            else:
                logger.warning(f"Invalid token for user activation from {ip_address}: {user.id}")
                return Response(
                    {"message": "유효하지 않은 인증 링크입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (TypeError, ValueError, OverflowError) as e:
            logger.error(f"User activation error from {ip_address}: {str(e)}")
            return Response(
                {"message": "유효하지 않은 인증 링크입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip