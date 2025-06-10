from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from accountbook.models import Account, TransactionHistory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext

User = get_user_model()


class Command(BaseCommand):
    help = 'N+1 문제 테스트 및 쿼리 수 비교 with dummy data and DB reset (조건 Prefetch 포함)'

    def handle(self, *args, **kwargs):
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(email='test@example.com', password='test1234')

        self.stdout.write("기존 데이터 삭제 중...")
        TransactionHistory.objects.filter(account__user=user).delete()
        Account.objects.filter(user=user).delete()

        self.stdout.write("더미 데이터 생성 중...")
        for i in range(100):
            account, created = Account.objects.get_or_create(
                user=user,
                account_number=f"ACC{i}",
                defaults={'bank_code': '001', 'account_type': 'CHECKING', 'balance': 0}
            )
            for j in range(50):
                TransactionHistory.objects.create(
                    account=account,
                    transaction_amount=1000 + j * 100,
                    post_transaction_amount=1000 + j * 100,
                    transaction_details=f"거래내역 {j} for 계좌 {i}",
                    transaction_type='DEPOSIT' if j % 2 == 0 else 'WITHDRAW',
                    transaction_method='ATM',
                    transaction_timestamp=timezone.now() - timedelta(days=j),
                )

        # 쿼리 로그 초기화 및 디버깅 함수
        def log_queries(description, queries):
            self.stdout.write(f"\n--- {description} ---")
            for i, query in enumerate(queries):
                self.stdout.write(f"{i + 1}. {query['sql'][:80]}...")
            self.stdout.write(f"총 쿼리 수: {len(queries)}\n")

        # 1. N+1 문제 (최적화 전) - 격리된 테스트
        with CaptureQueriesContext(connection) as ctx1:
            accounts = Account.objects.filter(user=user)
            for account in accounts:
                for transaction in account.transactions.all():
                    _ = transaction.transaction_amount

        self.stdout.write(f"최적화 전 쿼리 수: {len(ctx1.captured_queries)}")
        log_queries("최적화 전 쿼리", ctx1.captured_queries)

        # 2. 단순 prefetch_related (최적화) - 격리된 테스트
        with CaptureQueriesContext(connection) as ctx2:
            accounts_optimized = Account.objects.filter(user=user).prefetch_related('transactions')
            for account in accounts_optimized:
                for transaction in account.transactions.all():
                    _ = transaction.transaction_amount

        self.stdout.write(f"최적화 후 쿼리 수(모든 거래): {len(ctx2.captured_queries)}")
        log_queries("prefetch_related 쿼리", ctx2.captured_queries)

        # 3. 조건 Prefetch 적용 (transaction_type='DEPOSIT') - 격리된 테스트
        with CaptureQueriesContext(connection) as ctx3:
            deposit_qs = TransactionHistory.objects.filter(transaction_type='DEPOSIT')
            accounts_prefetch = Account.objects.filter(user=user).prefetch_related(
                Prefetch('transactions', queryset=deposit_qs, to_attr='deposit_transactions')
            )
            for account in accounts_prefetch:
                # 수정된 부분: account.transactions.all() 대신 account.deposit_transactions 사용
                for transaction in account.deposit_transactions:
                    _ = transaction.transaction_amount

        self.stdout.write(f"조건 Prefetch(입금만) 쿼리 수: {len(ctx3.captured_queries)}")
        log_queries("조건부 Prefetch 쿼리", ctx3.captured_queries)

        # 추가 테스트: 다른 관계에 접근하지 않는지 확인
        with CaptureQueriesContext(connection) as ctx4:
            # 모든 관련 데이터를 한 번에 prefetch
            accounts_full = Account.objects.filter(user=user).select_related('user').prefetch_related(
                'transactions'
            )
            for account in accounts_full:
                # user 정보와 transactions 정보만 접근
                _ = account.user.email
                for transaction in account.transactions.all():
                    _ = transaction.transaction_amount

        self.stdout.write(f"완전 최적화 쿼리 수: {len(ctx4.captured_queries)}")
        log_queries("완전 최적화 쿼리", ctx4.captured_queries)