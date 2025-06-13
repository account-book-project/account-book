from django.urls import path

from accountbook.views.transactions_views import (
    TransactionDetailView,
    TransactionListCreateView,
)

urlpatterns = [
    path(
        'accounts/<int:account_id>/transactions/',
        TransactionListCreateView.as_view(),
        name='transaction_list_create',
    ),
    path(
        'accounts/<int:account_id>/transactions/<int:pk>/',
        TransactionDetailView.as_view(),
        name='transaction_detail',
    ),
]
