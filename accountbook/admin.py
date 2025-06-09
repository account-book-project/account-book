from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Account, TransactionHistory, Analysis, Notification

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'nickname', 'name', 'phone_number', 'is_active', 'is_staff', 'last_login')
    search_fields = ('email', 'nickname', 'name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('nickname', 'name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'bank_code', 'account_type', 'balance')
    search_fields = ('account_number',)
    list_filter = ('bank_code', 'account_type')

@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_amount', 'transaction_type', 'transaction_method', 'transaction_timestamp')
    search_fields = ('transaction_details',)
    list_filter = ('transaction_type', 'transaction_method')
    ordering = ('-transaction_timestamp',)

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'analysis_target', 'analysis_period', 'start_date', 'end_date')
    list_filter = ('analysis_target', 'analysis_period')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('message',)
