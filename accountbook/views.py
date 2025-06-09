# accountbook/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.shortcuts import get_object_or_404

from .models import Account, TransactionHistory
from .serializers import (
    SignupSerializer, UserSerializer, UserUpdateSerializer,
    AccountSerializer, AccountCreateSerializer,
    TransactionHistorySerializer, TransactionCreateSerializer
)


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="회원가입",
        description="새로운 사용자를 생성합니다.",
        responses={201: {"type": "object", "properties": {
            "message": {"type": "string"},
            "user_id": {"type": "integer"}
        }}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "회원가입이 완료되었습니다.",
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 정보 조회",
        description="로그인한 사용자의 정보를 조회합니다.",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="내 정보 수정",
        description="로그인한 사용자의 정보를 수정합니다.",
        request=UserUpdateSerializer,
        responses={200: {"type": "object", "properties": {
            "message": {"type": "string"}
        }}}
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "회원 정보가 수정되었습니다."
        })


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
        responses={200: AccountSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="계좌 생성",
        description="새로운 계좌를 생성합니다.",
        request=AccountCreateSerializer,
        responses={201: {"type": "object", "properties": {
            "message": {"type": "string"},
            "account_id": {"type": "integer"}
        }}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()

        return Response({
            "message": "계좌가 성공적으로 생성되었습니다.",
            "account_id": account.id
        }, status=status.HTTP_201_CREATED)


class TransactionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionHistorySerializer

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        account = get_object_or_404(Account, id=account_id, user=self.request.user)
        return TransactionHistory.objects.filter(account=account).order_by('-transaction_timestamp')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        account_id = self.kwargs.get('account_id')
        context['account'] = get_object_or_404(Account, id=account_id, user=self.request.user)
        return context

    @extend_schema(
        summary="거래내역 목록 조회",
        description="특정 계좌의 거래내역 목록을 조회합니다.",
        responses={200: TransactionHistorySerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="거래내역 생성",
        description="특정 계좌에 새로운 거래내역을 생성합니다.",
        request=TransactionCreateSerializer,
        responses={201: {"type": "object", "properties": {
            "message": {"type": "string"},
            "transaction_id": {"type": "integer"}
        }}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()

        return Response({
            "message": "거래내역이 성공적으로 추가되었습니다.",
            "transaction_id": transaction.id
        }, status=status.HTTP_201_CREATED)
