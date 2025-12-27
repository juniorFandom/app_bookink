from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.business.models import Business
from .models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction

User = get_user_model()


class UserWalletSerializer(serializers.ModelSerializer):
    """Serializer pour les wallets utilisateur."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserWallet
        fields = [
            'id', 'user', 'user_username', 'user_email', 'user_full_name',
            'balance', 'currency', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['balance', 'created_at', 'updated_at']
    
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class BusinessWalletSerializer(serializers.ModelSerializer):
    """Serializer pour les wallets entreprise."""
    
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_description = serializers.CharField(source='business.description', read_only=True)
    
    class Meta:
        model = BusinessWallet
        fields = [
            'id', 'business', 'business_name', 'business_description',
            'balance', 'currency', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['balance', 'created_at', 'updated_at']


class UserTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions utilisateur."""
    
    wallet_owner = serializers.CharField(source='wallet.user.username', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserTransaction
        fields = [
            'id', 'wallet', 'wallet_owner', 'transaction_type', 'transaction_type_display',
            'amount', 'status', 'status_display', 'reference', 'description',
            'related_transaction', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'created_at', 'updated_at']


class BusinessTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions entreprise."""
    
    wallet_owner = serializers.CharField(source='wallet.business.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BusinessTransaction
        fields = [
            'id', 'wallet', 'wallet_owner', 'transaction_type', 'transaction_type_display',
            'amount', 'status', 'status_display', 'reference', 'description',
            'related_transaction', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'created_at', 'updated_at']


class DepositSerializer(serializers.Serializer):
    """Serializer pour les dépôts."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value


class WithdrawalSerializer(serializers.Serializer):
    """Serializer pour les retraits."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value


class TransferSerializer(serializers.Serializer):
    """Serializer pour les transferts."""
    
    recipient_type = serializers.ChoiceField(choices=[('user', 'User'), ('business', 'Business')])
    recipient_identifier = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value
    
    def validate_recipient_identifier(self, value):
        recipient_type = self.initial_data.get('recipient_type')
        
        if recipient_type == 'user':
            try:
                user = User.objects.get(username=value)
                UserWallet.objects.get(user=user)
            except (User.DoesNotExist, UserWallet.DoesNotExist):
                raise serializers.ValidationError("User not found or has no wallet.")
        elif recipient_type == 'business':
            try:
                business = Business.objects.get(name=value)
                BusinessWallet.objects.get(business=business)
            except (Business.DoesNotExist, BusinessWallet.DoesNotExist):
                raise serializers.ValidationError("Business not found or has no wallet.")
        
        return value


class WalletStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de wallet."""
    
    total_transactions = serializers.IntegerField()
    total_deposits = serializers.IntegerField()
    total_withdrawals = serializers.IntegerField()
    total_transfers = serializers.IntegerField()
    total_payments = serializers.IntegerField()
    completed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()


class TransactionStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de transactions."""
    
    total_amount_deposited = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount_withdrawn = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount_transferred_out = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount_transferred_in = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_transactions_count = serializers.IntegerField()
    completed_transactions_count = serializers.IntegerField()
    failed_transactions_count = serializers.IntegerField()
    cancelled_transactions_count = serializers.IntegerField()


class WalletDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les wallets avec transactions récentes."""
    
    recent_transactions = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = UserWallet
        fields = [
            'id', 'user', 'balance', 'currency', 'is_active',
            'recent_transactions', 'statistics', 'created_at', 'updated_at'
        ]
    
    def get_recent_transactions(self, obj):
        transactions = obj.transactions.all()[:10]  # 10 dernières transactions
        return UserTransactionSerializer(transactions, many=True).data
    
    def get_statistics(self, obj):
        from .services.wallet_service import WalletService
        stats = WalletService.get_wallet_statistics(obj)
        return WalletStatisticsSerializer(stats).data


class BusinessWalletDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les wallets entreprise avec transactions récentes."""
    
    recent_transactions = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessWallet
        fields = [
            'id', 'business', 'balance', 'currency', 'is_active',
            'recent_transactions', 'statistics', 'created_at', 'updated_at'
        ]
    
    def get_recent_transactions(self, obj):
        transactions = obj.transactions.all()[:10]  # 10 dernières transactions
        return BusinessTransactionSerializer(transactions, many=True).data
    
    def get_statistics(self, obj):
        from .services.wallet_service import WalletService
        stats = WalletService.get_wallet_statistics(obj)
        return WalletStatisticsSerializer(stats).data 