from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.business.models import Business
from ..models import UserWallet, BusinessWallet

User = get_user_model()


class WalletService:
    """Service métier pour la gestion des wallets."""
    
    @staticmethod
    def get_or_create_user_wallet(user):
        """Récupère ou crée un wallet pour un utilisateur."""
        wallet, created = UserWallet.objects.get_or_create(user=user)
        return wallet, created
    
    @staticmethod
    def get_or_create_business_wallet(business):
        """Récupère ou crée un wallet pour une entreprise."""
        wallet, created = BusinessWallet.objects.get_or_create(business=business)
        return wallet, created
    
    @staticmethod
    def get_user_wallet(user):
        """Récupère le wallet d'un utilisateur."""
        try:
            return UserWallet.objects.get(user=user)
        except UserWallet.DoesNotExist:
            return None
    
    @staticmethod
    def get_business_wallet(business):
        """Récupère le wallet d'une entreprise."""
        try:
            return BusinessWallet.objects.get(business=business)
        except BusinessWallet.DoesNotExist:
            return None
    
    @staticmethod
    def get_wallet_by_id(wallet_id, wallet_type='user'):
        """Récupère un wallet par son ID."""
        if wallet_type == 'user':
            try:
                return UserWallet.objects.get(id=wallet_id)
            except UserWallet.DoesNotExist:
                return None
        elif wallet_type == 'business':
            try:
                return BusinessWallet.objects.get(id=wallet_id)
            except BusinessWallet.DoesNotExist:
                return None
        return None
    
    @staticmethod
    def update_wallet_balance(wallet, amount, operation='add'):
        """Met à jour le solde d'un wallet."""
        if not isinstance(wallet.balance, Decimal):
            wallet.balance = Decimal(str(wallet.balance))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if operation == 'add':
            wallet.balance += amount
        elif operation == 'subtract':
            if wallet.balance >= amount:
                wallet.balance -= amount
            else:
                raise ValueError(_('Insufficient funds'))
        else:
            raise ValueError(_('Invalid operation'))
        wallet.save()
        return wallet
    
    @staticmethod
    def check_sufficient_funds(wallet, amount):
        """Vérifie si le wallet a suffisamment de fonds."""
        return wallet.balance >= amount
    
    @staticmethod
    def deactivate_wallet(wallet):
        """Désactive un wallet."""
        wallet.is_active = False
        wallet.save()
        return wallet
    
    @staticmethod
    def activate_wallet(wallet):
        """Active un wallet."""
        wallet.is_active = True
        wallet.save()
        return wallet
    
    @staticmethod
    def change_currency(wallet, new_currency):
        """Change la devise d'un wallet."""
        wallet.currency = new_currency
        wallet.save()
        return wallet
    
    @staticmethod
    def get_wallet_statistics(wallet):
        """Récupère les statistiques d'un wallet."""
        transactions = wallet.transactions.all()
        
        stats = {
            'total_transactions': transactions.count(),
            'total_deposits': transactions.filter(transaction_type='DEPOSIT').count(),
            'total_withdrawals': transactions.filter(transaction_type='WITHDRAWAL').count(),
            'total_transfers': transactions.filter(transaction_type='TRANSFER').count(),
            'total_payments': transactions.filter(transaction_type='PAYMENT').count(),
            'completed_transactions': transactions.filter(status='COMPLETED').count(),
            'pending_transactions': transactions.filter(status='PENDING').count(),
            'failed_transactions': transactions.filter(status='FAILED').count(),
        }
        
        return stats
    
    @staticmethod
    def get_user_wallets_with_balance(min_balance=0):
        """Récupère tous les wallets utilisateur avec un solde minimum."""
        return UserWallet.objects.filter(
            balance__gte=min_balance,
            is_active=True
        ).select_related('user')
    
    @staticmethod
    def get_business_wallets_with_balance(min_balance=0):
        """Récupère tous les wallets entreprise avec un solde minimum."""
        return BusinessWallet.objects.filter(
            balance__gte=min_balance,
            is_active=True
        ).select_related('business') 