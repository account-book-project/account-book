# accountbook/views.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Account, TransactionHistory
from .serializers import (
    AccountCreateSerializer,
    AccountSerializer,
    SignupSerializer,
    TransactionCreateSerializer,
    TransactionHistorySerializer,
    UserSerializer,
    UserUpdateSerializer,
)

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
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {"message": "회원가입이 완료되었습니다.", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 정보 조회",
        description="로그인한 사용자의 정보를 조회합니다.",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="내 정보 수정",
        description="로그인한 사용자의 정보를 수정합니다.",
        request=UserUpdateSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "회원 정보가 수정되었습니다."})

    @extend_schema(
        summary="회원 탈퇴",
        description="회원 탈퇴 후 'Deleted successfully' 메시지를 반환합니다.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def delete(self, request):
        request.user.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)


class AccountListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AccountCreateSerializer
        return AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @extend_schema(
        summary="계좌 목록 조회",
        description="로그인한 사용자의 계좌 목록을 조회합니다.",
        responses={200: AccountSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="계좌 생성",
        description="새로운 계좌를 생성합니다.",
        request=AccountCreateSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "account_id": {"type": "integer"},
                },
            }
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()

        return Response(
            {"message": "계좌가 성공적으로 생성되었습니다.", "account_id": account.id},
            status=status.HTTP_201_CREATED,
        )


class TransactionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionHistorySerializer

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        account = get_object_or_404(Account, id=account_id, user=self.request.user)
        queryset = TransactionHistory.objects.filter(account=account)

        # 필터링 파라미터
        transaction_type = self.request.query_params.get('transaction_type')
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if transaction_type in ['DEPOSIT', 'WITHDRAW']:
            queryset = queryset.filter(transaction_type=transaction_type)
        if min_amount:
            queryset = queryset.filter(transaction_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(transaction_amount__lte=max_amount)
        if start_date:
            queryset = queryset.filter(
                transaction_timestamp__date__gte=parse_date(start_date)
            )
        if end_date:
            queryset = queryset.filter(
                transaction_timestamp__date__lte=parse_date(end_date)
            )

        return queryset.order_by('-transaction_timestamp')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        account_id = self.kwargs.get('account_id')
        context['account'] = get_object_or_404(
            Account, id=account_id, user=self.request.user
        )
        return context

    @extend_schema(
        summary="거래내역 목록 조회",
        description="특정 계좌의 거래내역 목록을 조회합니다. 거래유형, 금액범위, 날짜범위 필터링이 가능합니다.",
        parameters=[
            OpenApiParameter(
                name='transaction_type',
                description='거래 유형 (DEPOSIT / WITHDRAW)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='min_amount',
                description='최소 거래 금액',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='max_amount',
                description='최대 거래 금액',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='start_date',
                description='조회 시작일 (YYYY-MM-DD)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='end_date',
                description='조회 종료일 (YYYY-MM-DD)',
                required=False,
                type=str,
            ),
        ],
        responses={200: TransactionHistorySerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="거래내역 생성",
        description="특정 계좌에 새로운 거래내역을 생성합니다.",
        request=TransactionCreateSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "transaction_id": {"type": "integer"},
                },
            }
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()

        return Response(
            {
                "message": "거래내역이 성공적으로 추가되었습니다.",
                "transaction_id": transaction.id,
            },
            status=status.HTTP_201_CREATED,
        )


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
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh_token = response.data.get('refresh')
            access_token = response.data.get('access')

            response.data = {"message": "로그인 성공"}

            cookie_max_age = 60 * 60 * 24 * 7  # 7일

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

        return response


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
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # 블랙리스트 등록

        except Exception as e:
            # 블랙리스트 등록 실패해도 쿠키 삭제는 계속
            pass

        response = Response({"message": "로그아웃 성공"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


# 이메일 인증 처리
class ActivateUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {"message": "이메일 인증이 완료되었습니다."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "유효하지 않은 인증 링크입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# 계좌 삭제 API 구현
class AccountDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer
    lookup_url_kwarg = 'account_id'

    def get_queryset(self):
        # 본인 계좌만 삭제 가능
        return Account.objects.filter(user=self.request.user)

    @extend_schema(
        summary="계좌 삭제",
        description="특정 계좌를 삭제합니다. 본인의 계좌만 삭제할 수 있습니다.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "계좌가 삭제되었습니다."}, status=200)


# 거래내역 조회, 수정, 삭제
class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        return TransactionHistory.objects.filter(
            account__id=account_id, account__user=self.request.user
        )

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TransactionCreateSerializer
        return TransactionHistorySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        account_id = self.kwargs['account_id']
        context['account'] = get_object_or_404(
            Account, id=account_id, user=self.request.user
        )
        return context

    @extend_schema(
        summary="거래내역 상세 조회",
        responses={200: TransactionHistorySerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="거래내역 수정",
        request=TransactionCreateSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def patch(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({"message": "거래내역이 수정되었습니다."}, status=200)

    @extend_schema(
        summary="거래내역 삭제",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return Response({"message": "거래내역이 삭제되었습니다."}, status=200)
