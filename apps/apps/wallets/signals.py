from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import logging

from .models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNALS POUR LES WALLETS
# =============================================================================

@receiver(post_save, sender=UserWallet)
def user_wallet_post_save(sender, instance, created, **kwargs):
    """
    Signal post_save pour UserWallet.
    Actions après création ou mise à jour d'un wallet utilisateur.
    """
    if created:
        logger.info(f"Nouveau wallet utilisateur créé: {instance.user} (Balance: {instance.balance} {instance.currency})")
        # Ici vous pouvez ajouter des actions spécifiques à la création
        # Par exemple: envoyer un email de bienvenue, créer des notifications, etc.
    else:
        logger.info(f"Wallet utilisateur mis à jour: {instance.user} (Balance: {instance.balance} {instance.currency})")
        # Actions lors de la mise à jour du wallet


@receiver(post_delete, sender=UserWallet)
def user_wallet_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour UserWallet.
    Actions après suppression d'un wallet utilisateur.
    """
    logger.warning(f"Wallet utilisateur supprimé: {instance.user} (Balance: {instance.balance} {instance.currency})")
    # Actions de nettoyage ou de log après suppression


@receiver(post_save, sender=BusinessWallet)
def business_wallet_post_save(sender, instance, created, **kwargs):
    """
    Signal post_save pour BusinessWallet.
    Actions après création ou mise à jour d'un wallet business.
    """
    if created:
        logger.info(f"Nouveau wallet business créé: {instance.business.name} (Balance: {instance.balance} {instance.currency})")
        # Actions spécifiques à la création d'un wallet business
    else:
        logger.info(f"Wallet business mis à jour: {instance.business.name} (Balance: {instance.balance} {instance.currency})")
        # Actions lors de la mise à jour du wallet business


@receiver(post_delete, sender=BusinessWallet)
def business_wallet_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour BusinessWallet.
    Actions après suppression d'un wallet business.
    """
    logger.warning(f"Wallet business supprimé: {instance.business.name} (Balance: {instance.balance} {instance.currency})")
    # Actions de nettoyage ou de log après suppression


# =============================================================================
# SIGNALS POUR LES TRANSACTIONS
# =============================================================================

@receiver(post_save, sender=UserTransaction)
def user_transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal post_save pour UserTransaction.
    Actions après création ou mise à jour d'une transaction utilisateur.
    """
    if created:
        logger.info(f"Nouvelle transaction utilisateur créée: {instance.reference} - {instance.amount} {instance.wallet.currency}")
        # Actions spécifiques à la création d'une transaction
        # Par exemple: mise à jour automatique du solde, notifications, etc.
    else:
        logger.info(f"Transaction utilisateur mise à jour: {instance.reference} - Statut: {instance.status}")
        # Actions lors de la mise à jour d'une transaction
        
        # Exemple: Mise à jour automatique du solde du wallet selon le statut
        if instance.status == 'COMPLETED' and instance.transaction_type in ['DEPOSIT', 'PAYMENT']:
            # La transaction est complétée et c'est un dépôt ou paiement
            # Le solde du wallet devrait être mis à jour
            pass


@receiver(post_delete, sender=UserTransaction)
def user_transaction_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour UserTransaction.
    Actions après suppression d'une transaction utilisateur.
    """
    logger.warning(f"Transaction utilisateur supprimée: {instance.reference} - {instance.amount} {instance.wallet.currency}")
    # Actions de nettoyage ou de log après suppression
    # Attention: la suppression de transactions peut avoir des implications sur l'audit


@receiver(post_save, sender=BusinessTransaction)
def business_transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal post_save pour BusinessTransaction.
    Actions après création ou mise à jour d'une transaction business.
    """
    if created:
        logger.info(f"Nouvelle transaction business créée: {instance.reference} - {instance.amount} {instance.wallet.currency}")
        # Actions spécifiques à la création d'une transaction business
    else:
        logger.info(f"Transaction business mise à jour: {instance.reference} - Statut: {instance.status}")
        # Actions lors de la mise à jour d'une transaction business
        
        # Exemple: Mise à jour automatique du solde du wallet selon le statut
        if instance.status == 'COMPLETED' and instance.transaction_type in ['DEPOSIT', 'PAYMENT']:
            # La transaction est complétée et c'est un dépôt ou paiement
            # Le solde du wallet devrait être mis à jour
            pass


@receiver(post_delete, sender=BusinessTransaction)
def business_transaction_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour BusinessTransaction.
    Actions après suppression d'une transaction business.
    """
    logger.warning(f"Transaction business supprimée: {instance.reference} - {instance.amount} {instance.wallet.currency}")
    # Actions de nettoyage ou de log après suppression
    # Attention: la suppression de transactions peut avoir des implications sur l'audit


# =============================================================================
# FONCTIONS UTILITAIRES POUR LES SIGNALS
# =============================================================================

def update_wallet_balance_on_transaction_completion(transaction):
    """
    Fonction utilitaire pour mettre à jour le solde du wallet
    quand une transaction est marquée comme complétée.
    """
    if transaction.status == 'COMPLETED':
        wallet = transaction.wallet
        
        if transaction.transaction_type == 'DEPOSIT':
            wallet.deposit(transaction.amount)
        elif transaction.transaction_type == 'WITHDRAWAL':
            wallet.withdraw(transaction.amount)
        elif transaction.transaction_type == 'PAYMENT':
            # Pour les paiements, la logique dépend du contexte
            # Par exemple: débit pour l'émetteur, crédit pour le destinataire
            pass
        
        logger.info(f"Solde du wallet mis à jour après transaction {transaction.reference}")


def send_transaction_notification(transaction):
    """
    Fonction utilitaire pour envoyer des notifications
    lors de la création ou mise à jour de transactions.
    """
    # Ici vous pouvez implémenter l'envoi de notifications
    # Par exemple: email, SMS, push notification, etc.
    pass 