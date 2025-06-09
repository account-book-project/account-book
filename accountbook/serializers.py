# accountbook/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .constants import ACCOUNT_TYPE, BANK_CODES, TRANSACTION_METHOD, TRANSACTION_TYPE
from .models import Account, TransactionHistory
from .utils import send_verification_email

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'nickname', 'name', 'phone_number']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'required': True},
            'nickname': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_nickname(self, value):
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        send_verification_email(user)  # 이메일전송

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'name', 'phone_number', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'name', 'phone_number']

    def validate_nickname(self, value):
        user = self.context['request'].user
        if User.objects.filter(nickname=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value


class AccountSerializer(serializers.ModelSerializer):
    bank_name = serializers.SerializerMethodField()
    account_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id',
            'account_number',
            'bank_code',
            'bank_name',
            'account_type',
            'account_type_name',
            'balance',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'balance',
            'created_at',
            'bank_name',
            'account_type_name',
        ]

    def get_bank_name(self, obj):
        return dict(BANK_CODES).get(obj.bank_code, '알 수 없음')

    def get_account_type_name(self, obj):
        return dict(ACCOUNT_TYPE).get(obj.account_type, '기타')


class AccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['account_number', 'bank_code', 'account_type']

    def validate_bank_code(self, value):
        valid_codes = [code for code, _ in BANK_CODES]
        if value not in valid_codes:
            raise serializers.ValidationError("유효하지 않은 은행 코드입니다.")
        return value

    def validate_account_type(self, value):
        valid_types = [type_code for type_code, _ in ACCOUNT_TYPE]
        if value not in valid_types:
            raise serializers.ValidationError("유효하지 않은 계좌 유형입니다.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['balance'] = 0  # 초기 잔액 0으로 설정
        return super().create(validated_data)


class TransactionHistorySerializer(serializers.ModelSerializer):
    transaction_type_name = serializers.SerializerMethodField()
    transaction_method_name = serializers.SerializerMethodField()

    class Meta:
        model = TransactionHistory
        fields = [
            'id',
            'transaction_amount',
            'post_transaction_amount',
            'transaction_details',
            'transaction_type',
            'transaction_type_name',
            'transaction_method',
            'transaction_method_name',
            'transaction_timestamp',
        ]
        read_only_fields = [
            'id',
            'post_transaction_amount',
            'transaction_type_name',
            'transaction_method_name',
        ]

    def get_transaction_type_name(self, obj):
        return dict(TRANSACTION_TYPE).get(obj.transaction_type, '기타')

    def get_transaction_method_name(self, obj):
        return dict(TRANSACTION_METHOD).get(obj.transaction_method, '기타')


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionHistory
        fields = [
            'transaction_amount',
            'transaction_details',
            'transaction_type',
            'transaction_method',
            'transaction_timestamp',
        ]

    def validate_transaction_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("거래 금액은 0보다 커야 합니다.")
        return value

    def validate_transaction_type(self, value):
        valid_types = [type_code for type_code, _ in TRANSACTION_TYPE]
        if value not in valid_types:
            raise serializers.ValidationError("유효하지 않은 거래 유형입니다.")
        return value

    def validate_transaction_method(self, value):
        valid_methods = [method_code for method_code, _ in TRANSACTION_METHOD]
        if value not in valid_methods:
            raise serializers.ValidationError("유효하지 않은 거래 방법입니다.")
        return value

    def create(self, validated_data):
        account = self.context['account']

        # 거래 금액과 타입에 따라 계좌 잔액 업데이트
        amount = validated_data['transaction_amount']
        transaction_type = validated_data['transaction_type']

        if transaction_type == 'DEPOSIT':
            account.balance += amount
        elif transaction_type == 'WITHDRAW':
            if account.balance < amount:
                raise serializers.ValidationError("잔액이 부족합니다.")
            account.balance -= amount

        account.save()

        # 거래 후 잔액 설정
        validated_data['account'] = account
        validated_data['post_transaction_amount'] = account.balance

        return super().create(validated_data)
