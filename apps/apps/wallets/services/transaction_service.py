import uuid
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from ..models import UserTransaction, BusinessTransaction, UserWallet, BusinessWallet
from .wallet_service import WalletService

User = get_user_model()


class TransactionService:
    """Service métier pour la gestion des transactions."""

    @staticmethod
    def generate_reference():
        """Génère une référence unique pour une transaction."""
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def create_user_transaction(wallet, transaction_type, amount, description='', status='PENDING'):
        """Crée une transaction utilisateur."""
        if not isinstance(wallet, UserWallet):
            raise ValueError(_('Invalid wallet type. Expected UserWallet.'))
        
        transaction = UserTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            status=status,
            reference=TransactionService.generate_reference()
        )
        return transaction

    @staticmethod
    def create_business_transaction(wallet, transaction_type, amount, description='', status='PENDING'):
        """Crée une transaction entreprise."""
        if not isinstance(wallet, BusinessWallet):
            raise ValueError(_('Invalid wallet type. Expected BusinessWallet.'))
        
        transaction = BusinessTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            status=status,
            reference=TransactionService.generate_reference()
        )
        return transaction

    @staticmethod
    def process_deposit(wallet, amount, description=''):
        """Traite un dépôt sur un wallet."""
        with db_transaction.atomic():
            # Créer la transaction
            if isinstance(wallet, UserWallet):
                transaction = TransactionService.create_user_transaction(
                    wallet, 'DEPOSIT', amount, description, 'PENDING'
                )
            else:
                transaction = TransactionService.create_business_transaction(
                    wallet, 'DEPOSIT', amount, description, 'PENDING'
                )
            
            # Mettre à jour le solde
            WalletService.update_wallet_balance(wallet, amount, 'add')
            
            # Marquer comme complétée
            transaction.mark_as_completed()
            
            return transaction

    @staticmethod
    def process_withdrawal(wallet, amount, description=''):
        """Traite un retrait d'un wallet."""
        with db_transaction.atomic():
            # Vérifier les fonds suffisants
            if not WalletService.check_sufficient_funds(wallet, amount):
                raise ValueError(_('Insufficient funds for withdrawal'))
            
            # Créer la transaction
            if isinstance(wallet, UserWallet):
                transaction = TransactionService.create_user_transaction(
                    wallet, 'WITHDRAWAL', amount, description, 'PENDING'
                )
            else:
                transaction = TransactionService.create_business_transaction(
                    wallet, 'WITHDRAWAL', amount, description, 'PENDING'
                )
            
            # Mettre à jour le solde
            WalletService.update_wallet_balance(wallet, amount, 'subtract')
            
            # Marquer comme complétée
            transaction.mark_as_completed()
            
            return transaction

    @staticmethod
    def process_transfer(sender_wallet, recipient_wallet, amount, description=''):
        """Traite un transfert entre deux wallets."""
        with db_transaction.atomic():
            # Vérifier les fonds suffisants
            if not WalletService.check_sufficient_funds(sender_wallet, amount):
                raise ValueError(_('Insufficient funds for transfer'))
            
            # Créer la transaction de sortie
            if isinstance(sender_wallet, UserWallet):
                outgoing_transaction = TransactionService.create_user_transaction(
                    sender_wallet, 'TRANSFER', amount, f"Transfer to {recipient_wallet.owner_repr}: {description}", 'PENDING'
                )
            else:
                outgoing_transaction = TransactionService.create_business_transaction(
                    sender_wallet, 'TRANSFER', amount, f"Transfer to {recipient_wallet.owner_repr}: {description}", 'PENDING'
                )
            
            # Créer la transaction d'entrée
            if isinstance(recipient_wallet, UserWallet):
                incoming_transaction = TransactionService.create_user_transaction(
                    recipient_wallet, 'TRANSFER', amount, f"Transfer from {sender_wallet.owner_repr}: {description}", 'PENDING'
                )
            else:
                incoming_transaction = TransactionService.create_business_transaction(
                    recipient_wallet, 'TRANSFER', amount, f"Transfer from {sender_wallet.owner_repr}: {description}", 'PENDING'
                )
            
            # Lier les transactions
            outgoing_transaction.related_transaction = incoming_transaction
            incoming_transaction.related_transaction = outgoing_transaction
            
            # Mettre à jour les soldes
            WalletService.update_wallet_balance(sender_wallet, amount, 'subtract')
            WalletService.update_wallet_balance(recipient_wallet, amount, 'add')
            
            # Marquer comme complétées
            outgoing_transaction.mark_as_completed()
            incoming_transaction.mark_as_completed()
            
            return outgoing_transaction, incoming_transaction

    @staticmethod
    def get_transaction_by_reference(reference):
        """Récupère une transaction par sa référence."""
        # Essayer d'abord les transactions utilisateur
        try:
            return UserTransaction.objects.get(reference=reference)
        except UserTransaction.DoesNotExist:
            pass
        
        # Essayer les transactions entreprise
        try:
            return BusinessTransaction.objects.get(reference=reference)
        except BusinessTransaction.DoesNotExist:
            pass
        
        return None

    @staticmethod
    def get_wallet_transactions(wallet, limit=None):
        """Récupère toutes les transactions d'un wallet."""
        transactions = wallet.transactions.all()
        if limit:
            transactions = transactions[:limit]
        return transactions

    @staticmethod
    def get_transactions_by_type(wallet, transaction_type, limit=None):
        """Récupère les transactions d'un type spécifique pour un wallet."""
        transactions = wallet.transactions.filter(transaction_type=transaction_type)
        if limit:
            transactions = transactions[:limit]
        return transactions

    @staticmethod
    def get_transactions_by_status(wallet, status, limit=None):
        """Récupère les transactions d'un statut spécifique pour un wallet."""
        transactions = wallet.transactions.filter(status=status)
        if limit:
            transactions = transactions[:limit]
        return transactions

    @staticmethod
    def cancel_transaction(transaction):
        """Annule une transaction."""
        if transaction.status == 'COMPLETED':
            # Si la transaction est complétée, on doit rembourser
            if transaction.transaction_type == 'DEPOSIT':
                WalletService.update_wallet_balance(transaction.wallet, transaction.amount, 'subtract')
            elif transaction.transaction_type == 'WITHDRAWAL':
                WalletService.update_wallet_balance(transaction.wallet, transaction.amount, 'add')
            elif transaction.transaction_type == 'TRANSFER':
                # Pour les transferts, on doit gérer les deux wallets
                if transaction.related_transaction:
                    related = transaction.related_transaction
                    if transaction.amount > 0:  # Transaction sortante
                        WalletService.update_wallet_balance(transaction.wallet, transaction.amount, 'add')
                        WalletService.update_wallet_balance(related.wallet, transaction.amount, 'subtract')
                    else:  # Transaction entrante
                        WalletService.update_wallet_balance(transaction.wallet, abs(transaction.amount), 'subtract')
                        WalletService.update_wallet_balance(related.wallet, abs(transaction.amount), 'add')
        
        transaction.mark_as_cancelled()
        return transaction

    @staticmethod
    def get_transaction_statistics(wallet):
        """Récupère les statistiques des transactions d'un wallet."""
        transactions = wallet.transactions.all()
        
        stats = {
            'total_amount_deposited': sum(t.amount for t in transactions.filter(transaction_type='DEPOSIT', status='COMPLETED')),
            'total_amount_withdrawn': sum(t.amount for t in transactions.filter(transaction_type='WITHDRAWAL', status='COMPLETED')),
            'total_amount_transferred_out': sum(t.amount for t in transactions.filter(transaction_type='TRANSFER', status='COMPLETED')),
            'total_amount_transferred_in': sum(t.amount for t in transactions.filter(transaction_type='TRANSFER', status='COMPLETED')),
            'pending_transactions_count': transactions.filter(status='PENDING').count(),
            'completed_transactions_count': transactions.filter(status='COMPLETED').count(),
            'failed_transactions_count': transactions.filter(status='FAILED').count(),
            'cancelled_transactions_count': transactions.filter(status='CANCELLED').count(),
        }
        
        return stats 