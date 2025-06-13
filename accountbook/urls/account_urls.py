from django.urls import path

from accountbook.views.accounts_views import AccountDetailView, AccountListCreateView

urlpatterns = [
    path('', AccountListCreateView.as_view(), name='account_list_create'),
    path('<int:account_id>/', AccountDetailView.as_view(), name='account_detail'),
]
