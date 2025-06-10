from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accountbook.models import Account, TransactionHistory

User = get_user_model()


class TransactionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser2@example.com", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            user=self.user,
            account_number="9999",
            bank_code="001",
            account_type="CHECKING",
        )

    def test_create_transaction(self):
        url = reverse('transaction_list_create', kwargs={'account_id': self.account.id})
        data = {
            "transaction_amount": 10000,
            "transaction_details": "월급 입금",
            "transaction_type": "DEPOSIT",
            "transaction_method": "ATM",
            "transaction_timestamp": "2025-06-10T10:00:00Z",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransactionHistory.objects.count(), 1)
        transaction = TransactionHistory.objects.first()
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.transaction_amount, 10000)

    def test_get_transaction_list(self):
        TransactionHistory.objects.create(
            account=self.account,
            transaction_amount=1000,
            post_transaction_amount=1000,
            transaction_details="테스트 입금",
            transaction_type="DEPOSIT",
            transaction_method="ATM",
            transaction_timestamp="2025-06-09T10:00:00Z",
        )
        url = reverse('transaction_list_create', kwargs={'account_id': self.account.id})
        response = self.client.get(url)
        print("Transaction List Response Data:", response.data)  # ← 출력 추가
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_delete_transaction(self):
        transaction = TransactionHistory.objects.create(
            account=self.account,
            transaction_amount=500,
            post_transaction_amount=500,
            transaction_details="테스트 출금",
            transaction_type="WITHDRAW",
            transaction_method="ONLINE",
            transaction_timestamp="2025-06-09T11:00:00Z",
        )
        url = reverse(
            'transaction_detail',
            kwargs={'account_id': self.account.id, 'pk': transaction.id},
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TransactionHistory.objects.count(), 0)
