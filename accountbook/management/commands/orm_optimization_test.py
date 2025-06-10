from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model
from accountbook.models import Account, TransactionHistory
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'ORM 최적화 기능 테스트 및 쿼리 수 비교'

    def handle(self, *args, **kwargs):
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(email='opt@test.com', password='test1234')

        # 기존 데이터 삭제 (초기화)
        self.stdout.write("기존 데이터 삭제 중...")
        TransactionHistory.objects.filter(account__user=user).delete()
        Account.objects.filter(user=user).delete()

        # 더미 데이터 생성
        self.stdout.write("더미 데이터 생성 중...")
        for i in range(3):
            account = Account.objects.create(
                user=user,
                account_number=f"OPT_ACC_{i}",
                bank_code='001',
                account_type='CHECKING',
                balance=0,
            )
            for j in range(5):
                TransactionHistory.objects.create(
                    account=account,
                    transaction_amount=1000 + j * 100,
                    post_transaction_amount=1000 + j * 100,
                    transaction_details=f"테스트 거래 {j} for 계좌 {i}",
                    transaction_type='DEPOSIT',
                    transaction_method='ATM',
                    transaction_timestamp=timezone.now() - timedelta(days=j),
                )

        # annotate 테스트
        connection.queries.clear()
        accounts = Account.objects.filter(user=user).annotate(transaction_count=Count('transactions'))
        list(accounts)
        self.stdout.write(f"Annotate 쿼리 수: {len(connection.queries)}")

        # aggregate 테스트
        connection.queries.clear()
        total = TransactionHistory.objects.filter(account__user=user).aggregate(total_amount=Sum('transaction_amount'))
        self.stdout.write(f"Aggregate 쿼리 수: {len(connection.queries)}")
        self.stdout.write(f"Aggregate 총합: {total['total_amount']}")

        # values 테스트
        connection.queries.clear()
        vals = Account.objects.filter(user=user).values('account_number', 'balance')
        list(vals)
        self.stdout.write(f"Values 쿼리 수: {len(connection.queries)}")

        # only 테스트
        connection.queries.clear()
        only_qs = Account.objects.filter(user=user).only('account_number')
        list(only_qs)
        self.stdout.write(f"Only 쿼리 수: {len(connection.queries)}")

        # defer 테스트
        connection.queries.clear()
        defer_qs = Account.objects.filter(user=user).defer('balance')
        list(defer_qs)
        self.stdout.write(f"Defer 쿼리 수: {len(connection.queries)}")
