from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'currency', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('balance', 'created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'balance', 'currency', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent wallet deletion for security


@admin.register(BusinessWallet)
class BusinessWalletAdmin(admin.ModelAdmin):
    list_display = ('business', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'currency', 'created_at')
    search_fields = ('business__name', 'business__description')
    readonly_fields = ('balance', 'created_at', 'updated_at')
    raw_id_fields = ('business',)
    
    fieldsets = (
        (None, {
            'fields': ('business', 'balance', 'currency', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent wallet deletion for security


@admin.register(UserTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'wallet', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at')
    raw_id_fields = ('related_transaction',)

    fieldsets = (
        (None, {
            'fields': ('wallet', 'transaction_type', 'amount', 'status', 'reference')
        }),
        (_('Additional Information'), {
            'fields': ('description', 'related_transaction')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent transaction deletion for security


@admin.register(BusinessTransaction)
class BusinessTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'wallet', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at', 'wallet__currency')
    search_fields = ('reference', 'wallet__business__name', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at')
    raw_id_fields = ('wallet', 'related_transaction')

    fieldsets = (
        (None, {
            'fields': ('wallet', 'transaction_type', 'amount', 'status', 'reference')
        }),
        (_('Additional Information'), {
            'fields': ('description', 'related_transaction')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent transaction deletion for security
