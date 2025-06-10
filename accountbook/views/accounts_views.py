# accountbook/views/accounts_views.py

import logging

from django.core.cache import cache
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Account
from ..permissions import IsAccountOwner
from ..serializers import AccountCreateSerializer, AccountSerializer

logger = logging.getLogger('accountbook.accounts')


class AccountListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AccountCreateSerializer
        return AccountSerializer

    def get_queryset(self):
        user = self.request.user
        cache_key = f'account_list_{user.id}'
        queryset = cache.get(cache_key)

        if not queryset:

            queryset = Account.objects.filter(user=user).only(
                'id',
                'account_number',
                'bank_code',
                'account_type',
                'balance',
                'created_at',
            )

            queryset_list = list(queryset)
            cache.set(cache_key, queryset_list, timeout=60 * 5)
            return queryset_list

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @extend_schema(
        summary="계좌 목록 조회",
        description="로그인한 사용자의 계좌 목록을 조회합니다.",
        responses={200: AccountSerializer(many=True)},
    )
    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        request._cache_update_cache = True
        request._cache_key = f'account_list_view_{request.user.id}'
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
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        cache_key = f'account_create_limit_{user_id}'
        create_count = cache.get(cache_key, 0)

        if create_count >= 5:
            logger.warning(f"Account creation rate limit exceeded for user {user_id}")
            return Response(
                {
                    "message": "계좌 생성 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            account = serializer.save()

            cache.set(cache_key, create_count + 1, timeout=60)
            cache.delete(f'account_list_{user_id}')
            logger.info(f"Account created: {account.id} by user {user_id}")

            return Response(
                {
                    "message": "계좌가 성공적으로 생성되었습니다.",
                    "account_id": account.id,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Account creation failed for user {user_id}: {str(e)}")
            return Response(
                {"message": "계좌 생성 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AccountDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAccountOwner]
    serializer_class = AccountSerializer
    lookup_url_kwarg = 'account_id'

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user).only(
            'id',
            'account_number',
            'bank_code',
            'account_type',
            'balance',
            'created_at',
            'user_id',
        )

    @extend_schema(
        summary="계좌 상세 조회",
        description="특정 계좌의 상세 정보를 조회합니다.",
        responses={200: AccountSerializer()},
    )
    def get(self, request, *args, **kwargs):
        account_id = kwargs.get('account_id')
        cache_key = f'account_detail_{account_id}_{request.user.id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().get(request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(cache_key, response.data, timeout=60 * 5)
        return response

    @extend_schema(
        summary="계좌 삭제",
        description="특정 계좌를 삭제합니다. 본인의 계좌만 삭제할 수 있습니다.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        user_id = request.user.id
        account_id = kwargs.get('account_id')

        try:
            instance = self.get_object()
            if instance.user.id != user_id:
                logger.warning(
                    f"Unauthorized account deletion attempt: User {user_id} tried to delete account {account_id}"
                )
                raise PermissionDenied("이 계좌를 삭제할 권한이 없습니다.")

            logger.info(f"Account deleted: {account_id} by user {user_id}")
            self.perform_destroy(instance)
            cache.delete(f'account_list_{user_id}')
            cache.delete(f'account_detail_{account_id}_{user_id}')
            return Response({"message": "계좌가 삭제되었습니다."}, status=200)
        except PermissionDenied as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(
                f"Account deletion failed: {account_id} by user {user_id}, error: {str(e)}"
            )
            return Response(
                {"message": "계좌 삭제 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
