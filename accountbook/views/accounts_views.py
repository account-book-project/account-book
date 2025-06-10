# accountbook/views/accounts_views.py

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Account
from ..serializers import AccountCreateSerializer, AccountSerializer


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
