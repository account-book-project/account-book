# accountbook/permissions.py

from rest_framework import permissions


class IsAccountOwner(permissions.BasePermission):
    # 계좌 소유자만 접근/수정/삭제 가능

    def has_object_permission(self, request, view, obj):
        # obj: Account 인스턴스
        return obj.user == request.user
