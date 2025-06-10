from django.urls import path

from accountbook.views.users_views import UserProfileView

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user_profile'),
]
