# oauth/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


# 닉네임 중복 확인용
class NicknameCheckSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20)

    def validate_nickname(self, value):
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value


# 실제 회원가입 시 닉네임 입력용
class NicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20)
