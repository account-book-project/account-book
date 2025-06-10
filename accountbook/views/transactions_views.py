# accountbook/views/transactions_views.py

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Account, TransactionHistory
from ..serializers import TransactionCreateSerializer, TransactionHistorySerializer


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
