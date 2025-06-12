# accountbook/serializers.py 최적화 진행 완료
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .constants import ACCOUNT_TYPE, BANK_CODES, TRANSACTION_METHOD, TRANSACTION_TYPE
from .models import Account, TransactionHistory
from .utils_common import send_verification_email

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
        if User.objects.filter(email=value).values('id').exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_nickname(self, value):
        if User.objects.filter(nickname=value).values('id').exists():
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
        if (
            User.objects.filter(nickname=value)
            .exclude(id=user.id)
            .values('id')
            .exists()
        ):
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value


class AccountSerializer(serializers.ModelSerializer):
    # 상수 딕셔너리 캐싱
    BANK_CODES_DICT = dict(BANK_CODES)
    ACCOUNT_TYPE_DICT = dict(ACCOUNT_TYPE)

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
        return self.BANK_CODES_DICT.get(obj.bank_code, '알 수 없음')

    def get_account_type_name(self, obj):
        return self.ACCOUNT_TYPE_DICT.get(obj.account_type, '기타')


class AccountCreateSerializer(serializers.ModelSerializer):
    # 유효한 코드와 타입을 클래스 변수로 캐싱
    VALID_BANK_CODES = [code for code, _ in BANK_CODES]
    VALID_ACCOUNT_TYPES = [type_code for type_code, _ in ACCOUNT_TYPE]

    class Meta:
        model = Account
        fields = ['account_number', 'bank_code', 'account_type']

    def validate_bank_code(self, value):
        if value not in self.VALID_BANK_CODES:
            raise serializers.ValidationError("유효하지 않은 은행 코드입니다.")
        return value

    def validate_account_type(self, value):
        if value not in self.VALID_ACCOUNT_TYPES:
            raise serializers.ValidationError("유효하지 않은 계좌 유형입니다.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['balance'] = 0  # 초기 잔액 0으로 설정
        return super().create(validated_data)


class TransactionHistorySerializer(serializers.ModelSerializer):
    # 상수 딕셔너리 캐싱
    TRANSACTION_TYPE_DICT = dict(TRANSACTION_TYPE)
    TRANSACTION_METHOD_DICT = dict(TRANSACTION_METHOD)

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
        return self.TRANSACTION_TYPE_DICT.get(obj.transaction_type, '기타')

    def get_transaction_method_name(self, obj):
        return self.TRANSACTION_METHOD_DICT.get(obj.transaction_method, '기타')


class TransactionCreateSerializer(serializers.ModelSerializer):
    # 유효한 타입과 방법을 클래스 변수로 캐싱
    VALID_TRANSACTION_TYPES = [type_code for type_code, _ in TRANSACTION_TYPE]
    VALID_TRANSACTION_METHODS = [method_code for method_code, _ in TRANSACTION_METHOD]

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
        if value not in self.VALID_TRANSACTION_TYPES:
            raise serializers.ValidationError("유효하지 않은 거래 유형입니다.")
        return value

    def validate_transaction_method(self, value):
        if value not in self.VALID_TRANSACTION_METHODS:
            raise serializers.ValidationError("유효하지 않은 거래 방법입니다.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        account = self.context['account']
        amount = validated_data['transaction_amount']
        transaction_type = validated_data['transaction_type']

        # F() 표현식을 사용하여 경쟁 상태 방지
        if transaction_type == 'DEPOSIT':
            Account.objects.filter(pk=account.pk).update(balance=F('balance') + amount)
        elif transaction_type == 'WITHDRAW':
            updated = Account.objects.filter(pk=account.pk, balance__gte=amount).update(
                balance=F('balance') - amount
            )
            if not updated:
                raise serializers.ValidationError("잔액이 부족합니다.")

        # 업데이트된 계좌 정보 다시 가져오기
        account.refresh_from_db()

        # 거래 후 잔액 설정
        validated_data['account'] = account
        validated_data['post_transaction_amount'] = account.balance

        return super().create(validated_data)
