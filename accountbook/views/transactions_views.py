# accountbook/views/transactions_views.py

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.db import transaction
from django.core.cache import cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from ..models import Account, TransactionHistory
from ..serializers import TransactionCreateSerializer, TransactionHistorySerializer


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TransactionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionHistorySerializer

    def get_account(self):
        """계좌 정보를 캐싱하여 반복 조회 방지"""
        account_id = self.kwargs.get('account_id')
        user_id = self.request.user.id

        # 캐시 키 생성
        cache_key = f'account_{account_id}_user_{user_id}'

        # 캐시에서 계좌 정보 조회
        account = cache.get(cache_key)

        if not account:
            # 캐시에 없으면 DB에서 조회
            account = get_object_or_404(Account, id=account_id, user=self.request.user)
            # 캐시에 저장 (5분 유효)
            cache.set(cache_key, account, timeout=60 * 5)

        return account

    def get_queryset(self):
        account = self.get_account()

        # 필터링 파라미터
        filters = Q(account=account)

        transaction_type = self.request.query_params.get('transaction_type')
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        # 필터링 조건 구성
        if transaction_type in ['DEPOSIT', 'WITHDRAW']:
            filters &= Q(transaction_type=transaction_type)
        if min_amount:
            filters &= Q(transaction_amount__gte=min_amount)
        if max_amount:
            filters &= Q(transaction_amount__lte=max_amount)
        if start_date:
            filters &= Q(transaction_timestamp__date__gte=parse_date(start_date))
        if end_date:
            filters &= Q(transaction_timestamp__date__lte=parse_date(end_date))

        # 최적화된 쿼리셋 반환
        return TransactionHistory.objects.filter(filters).select_related('account').only(
            'id', 'transaction_amount', 'post_transaction_amount',
            'transaction_details', 'transaction_type', 'transaction_method',
            'transaction_timestamp', 'account'
        ).order_by('-transaction_timestamp')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['account'] = self.get_account()
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
            OpenApiParameter(
                name='page',
                description='페이지 번호',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='page_size',
                description='페이지 크기 (최대 100)',
                required=False,
                type=int,
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
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_obj = serializer.save()

        # 계좌 캐시 무효화
        account_id = self.kwargs.get('account_id')
        user_id = request.user.id
        cache_key = f'account_{account_id}_user_{user_id}'
        cache.delete(cache_key)

        # 거래내역 목록 캐시 패턴 무효화 (안전 처리)
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f'transactions_{account_id}_*')

        return Response(
            {
                "message": "거래내역이 성공적으로 추가되었습니다.",
                "transaction_id": transaction_obj.id,
            },
            status=status.HTTP_201_CREATED,
        )


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_account(self):
        """계좌 정보를 캐싱하여 반복 조회 방지"""
        account_id = self.kwargs['account_id']
        user_id = self.request.user.id

        # 캐시 키 생성
        cache_key = f'account_{account_id}_user_{user_id}'

        # 캐시에서 계좌 정보 조회
        account = cache.get(cache_key)

        if not account:
            # 캐시에 없으면 DB에서 조회
            account = get_object_or_404(Account, id=account_id, user=self.request.user)
            # 캐시에 저장 (5분 유효)
            cache.set(cache_key, account, timeout=60 * 5)

        return account

    def get_object(self):
        """거래내역 객체 조회 최적화"""
        transaction_id = self.kwargs['pk']
        account_id = self.kwargs['account_id']

        # 캐시 키 생성
        cache_key = f'transaction_{transaction_id}_account_{account_id}'

        # 캐시에서 거래내역 조회
        transaction = cache.get(cache_key)

        if not transaction:
            # 캐시에 없으면 DB에서 조회
            queryset = self.get_queryset()
            transaction = get_object_or_404(queryset, pk=transaction_id)
            # 캐시에 저장 (5분 유효)
            cache.set(cache_key, transaction, timeout=60 * 5)

        return transaction

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        # select_related로 계좌 정보 미리 로드
        return TransactionHistory.objects.filter(
            account__id=account_id, account__user=self.request.user
        ).select_related('account').order_by('-transaction_timestamp')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TransactionCreateSerializer
        return TransactionHistorySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['account'] = self.get_account()
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
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)

        # 캐시 무효화
        transaction_id = self.kwargs['pk']
        account_id = self.kwargs['account_id']
        user_id = request.user.id

        # 거래내역 캐시 무효화
        cache_key = f'transaction_{transaction_id}_account_{account_id}'
        cache.delete(cache_key)

        # 계좌 캐시 무효화
        account_cache_key = f'account_{account_id}_user_{user_id}'
        cache.delete(account_cache_key)

        # 거래내역 목록 캐시 패턴 무효화 (안전 처리)
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f'transactions_{account_id}_*')

        return Response({"message": "거래내역이 수정되었습니다."}, status=200)

    @extend_schema(
        summary="거래내역 삭제",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        # 삭제 전에 캐시 무효화
        transaction_id = self.kwargs['pk']
        account_id = self.kwargs['account_id']
        user_id = request.user.id

        # 거래내역 캐시 무효화
        cache_key = f'transaction_{transaction_id}_account_{account_id}'
        cache.delete(cache_key)

        # 계좌 캐시 무효화
        account_cache_key = f'account_{account_id}_user_{user_id}'
        cache.delete(account_cache_key)

        # 거래내역 목록 캐시 패턴 무효화 (안전 처리)
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f'transactions_{account_id}_*')

        response = super().delete(request, *args, **kwargs)
        return Response({"message": "거래내역이 삭제되었습니다."}, status=200)
