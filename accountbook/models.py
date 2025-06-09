# models.py

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from .constants import (
    ACCOUNT_TYPE,
    ANALYSIS_ABOUT,
    ANALYSIS_TYPES,
    BANK_CODES,
    TRANSACTION_METHOD,
    TRANSACTION_TYPE,
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='이메일',
        max_length=255,
        unique=True,
    )
    nickname = models.CharField(verbose_name='닉네임', max_length=50, blank=True)
    name = models.CharField(verbose_name='이름', max_length=50, blank=True)
    phone_number = models.CharField(verbose_name='전화번호', max_length=20, blank=True)
    is_active = models.BooleanField(verbose_name='활성화 여부', default=True)
    is_staff = models.BooleanField(verbose_name='스태프 여부', default=False)
    is_admin = models.BooleanField(verbose_name='관리자 여부', default=False)
    last_login = models.DateTimeField(verbose_name='마지막 로그인', auto_now=True)
    date_joined = models.DateTimeField(verbose_name='가입일', default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'
        db_table = 'users'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin


class Account(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='사용자',
    )
    account_number = models.CharField(max_length=30, verbose_name='계좌번호')
    bank_code = models.CharField(
        max_length=3, choices=BANK_CODES, default='000', verbose_name='은행 코드'
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE,
        default='CHECKING',
        verbose_name='계좌 종류',
    )
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='잔액'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '계좌'
        verbose_name_plural = '계좌 목록'
        db_table = 'accounts'

    def __str__(self):
        bank_name = dict(BANK_CODES).get(self.bank_code, '알 수 없음')
        return f"{bank_name} - {self.account_number}"


class TransactionHistory(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='계좌',
    )
    transaction_amount = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='거래 금액'
    )
    post_transaction_amount = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='거래 후 잔액'
    )
    transaction_details = models.CharField(max_length=255, verbose_name='거래 내용')
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE, verbose_name='거래 타입'
    )
    transaction_method = models.CharField(
        max_length=20, choices=TRANSACTION_METHOD, verbose_name='거래 방법'
    )
    transaction_timestamp = models.DateTimeField(verbose_name='거래 시간')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='기록 생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '거래 내역'
        verbose_name_plural = '거래 내역 목록'
        db_table = 'transaction_history'
        ordering = ['-transaction_timestamp']

    def __str__(self):
        transaction_type = '입금' if self.transaction_type == 'DEPOSIT' else '출금'
        return f"{self.transaction_timestamp.strftime('%Y-%m-%d %H:%M')} - {transaction_type} {self.transaction_amount:,}원"


class Analysis(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='analyses',
        verbose_name='사용자',
    )
    analysis_target = models.CharField(
        max_length=20, choices=ANALYSIS_ABOUT, verbose_name='분석 대상'
    )
    analysis_period = models.CharField(
        max_length=20, choices=ANALYSIS_TYPES, verbose_name='분석 주기'
    )
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    description = models.TextField(verbose_name='설명', blank=True)
    result_image = models.ImageField(
        upload_to='analysis_results/', verbose_name='결과 이미지', blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '분석'
        verbose_name_plural = '분석 목록'
        db_table = 'analysis'

    def __str__(self):
        target = dict(ANALYSIS_ABOUT).get(self.analysis_target, '기타')
        period = dict(ANALYSIS_TYPES).get(self.analysis_period, '기타')
        return f"{target} {period} 분석 ({self.start_date} ~ {self.end_date})"


class Notification(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='사용자',
    )
    message = models.TextField(verbose_name='알림 내용')
    is_read = models.BooleanField(default=False, verbose_name='읽음 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        verbose_name = '알림'
        verbose_name_plural = '알림 목록'
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.message[:30]}... ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
