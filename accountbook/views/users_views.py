# accountbook/views/users_views.py

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import UserSerializer, UserUpdateSerializer

User = get_user_model()


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 정보 조회",
        description="로그인한 사용자의 정보를 조회합니다.",
        responses={200: UserSerializer},
    )
    def get(self, request):
        user_id = request.user.id
        cache_key = f'user_profile_{user_id}'

        # 캐시에서 사용자 정보 조회
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 캐시에 없으면 DB에서 조회 (필요한 필드만 선택)
        user = (
            User.objects.filter(id=user_id)
            .only('id', 'email', 'nickname', 'name', 'phone_number', 'date_joined')
            .first()
        )

        serializer = UserSerializer(user)

        # 캐시에 저장 (30분 유효)
        cache.set(cache_key, serializer.data, timeout=60 * 30)

        return Response(serializer.data)

    @extend_schema(
        summary="내 정보 수정",
        description="로그인한 사용자의 정보를 수정합니다.",
        request=UserUpdateSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    @transaction.atomic
    def patch(self, request):
        # 업데이트할 필드만 추출
        update_fields = {
            k: v
            for k, v in request.data.items()
            if k in ['nickname', 'name', 'phone_number']
        }

        serializer = UserUpdateSerializer(
            request.user, data=update_fields, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 캐시 무효화
        cache_key = f'user_profile_{request.user.id}'
        cache.delete(cache_key)

        return Response({"message": "회원 정보가 수정되었습니다."})

    @extend_schema(
        summary="회원 탈퇴",
        description="회원 탈퇴 후 'Deleted successfully' 메시지를 반환합니다.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
    )
    @transaction.atomic
    def delete(self, request):
        user_id = request.user.id

        # 소프트 삭제 패턴 적용 (실제 삭제 대신 is_active를 False로 설정)
        User.objects.filter(id=user_id).update(is_active=False)

        # 캐시 무효화
        cache_key = f'user_profile_{user_id}'
        cache.delete(cache_key)

        return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)
