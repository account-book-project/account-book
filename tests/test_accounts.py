from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accountbook.models import Account

User = get_user_model()


class AccountAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_account(self):
        url = reverse('account_list_create')
        data = {
            "account_number": "1234567890",
            "bank_code": "001",
            "account_type": "CHECKING",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Account.objects.first().user, self.user)

    def test_get_account_list(self):
        Account.objects.create(
            user=self.user,
            account_number="1111",
            bank_code="001",
            account_type="CHECKING",
        )
        Account.objects.create(
            user=self.user,
            account_number="2222",
            bank_code="002",
            account_type="SAVINGS",
        )
        url = reverse('account_list_create')
        response = self.client.get(url)
        print("Account List Response Data:", response.data)  # ← 여기에 출력 추가
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 만약 pagination 결과라면 아래처럼 변경할 수 있음
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_delete_account(self):
        account = Account.objects.create(
            user=self.user,
            account_number="3333",
            bank_code="001",
            account_type="CHECKING",
        )
        url = reverse('account_detail', kwargs={'account_id': account.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Account.objects.count(), 0)
