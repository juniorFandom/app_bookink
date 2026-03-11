#!/usr/bin/env python
"""
Script de test pour vérifier le bon fonctionnement du système de wallet
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from apps.business.models import Business, BusinessLocation
from apps.wallets.models.wallet import UserWallet, BusinessLocationWallet
from apps.wallets.models.transaction import UserTransaction, BusinessTransaction
from apps.wallets.services.wallet_service import WalletService
from apps.wallets.services.transaction_service import TransactionService

User = get_user_model()

def test_wallet_system():
    """Test complet du système de wallet"""
    print("=== TEST DU SYSTÈME DE WALLET ===\n")
    
    # 1. Vérifier les wallets existants
    print("1. Vérification des wallets existants:")
    user_wallets = UserWallet.objects.all()
    business_location_wallets = BusinessLocationWallet.objects.all()
    
    print(f"   - Wallets utilisateur: {user_wallets.count()}")
    print(f"   - Wallets business location: {business_location_wallets.count()}")
    
    # 2. Créer un utilisateur de test si nécessaire
    print("\n2. Création d'un utilisateur de test:")
    test_user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        print(f"   - Utilisateur créé: {test_user.username}")
    else:
        print(f"   - Utilisateur existant: {test_user.username}")
    
    # 3. Créer un business de test
    print("\n3. Création d'un business de test:")
    test_business, created = Business.objects.get_or_create(
        name='Test Business',
        defaults={
            'owner': test_user,
            'email': 'business@example.com',
            'phone': '+237123456789'
        }
    )
    if created:
        print(f"   - Business créé: {test_business.name}")
    else:
        print(f"   - Business existant: {test_business.name}")
    
    # 4. Créer une business location de test
    print("\n4. Création d'une business location de test:")
    test_location, created = BusinessLocation.objects.get_or_create(
        name='Test Hotel',
        business=test_business,
        defaults={
            'business_location_type': 'hotel',
            'phone': '+237123456789',
            'email': 'hotel@example.com',
            'city': 'Douala',
            'country': 'CM'
        }
    )
    if created:
        print(f"   - Location créée: {test_location.name}")
    else:
        print(f"   - Location existante: {test_location.name}")
    
    # 5. Vérifier/créer les wallets
    print("\n5. Vérification des wallets:")
    
    # Wallet utilisateur
    user_wallet, created = WalletService.get_or_create_user_wallet(test_user)
    if created:
        print(f"   - Wallet utilisateur créé: {user_wallet.id}")
    else:
        print(f"   - Wallet utilisateur existant: {user_wallet.id} (solde: {user_wallet.balance} XAF)")
    
    # Wallet business location
    business_location_wallet = getattr(test_location, 'wallet', None)
    if not business_location_wallet:
        business_location_wallet = BusinessLocationWallet.objects.create(business_location=test_location)
        print(f"   - Wallet business location créé: {business_location_wallet.id}")
    else:
        print(f"   - Wallet business location existant: {business_location_wallet.id} (solde: {business_location_wallet.balance} XAF)")
    
    # 6. Test des transactions
    print("\n6. Test des transactions:")
    
    # Dépôt sur le wallet utilisateur
    try:
        deposit_transaction = TransactionService.process_deposit(
            wallet=user_wallet,
            amount=Decimal('50000'),
            description="Test dépôt initial"
        )
        print(f"   - Dépôt utilisateur: {deposit_transaction.amount} XAF (référence: {deposit_transaction.reference})")
    except Exception as e:
        print(f"   - Erreur dépôt utilisateur: {e}")
    
    # Dépôt sur le wallet business location
    try:
        # Utiliser UserTransaction avec le wallet business location
        business_deposit = UserTransaction.objects.create(
            wallet=business_location_wallet,
            transaction_type='DEPOSIT',
            amount=Decimal('100000'),
            description="Test dépôt business location",
            status='COMPLETED',
            reference=f"TEST-DEP-{UserTransaction.objects.count() + 1}"
        )
        business_location_wallet.deposit(Decimal('100000'))
        print(f"   - Dépôt business location: {business_deposit.amount} XAF (référence: {business_deposit.reference})")
    except Exception as e:
        print(f"   - Erreur dépôt business location: {e}")
    
    # 7. Vérifier les soldes finaux
    print("\n7. Soldes finaux:")
    user_wallet.refresh_from_db()
    business_location_wallet.refresh_from_db()
    
    print(f"   - Solde utilisateur: {user_wallet.balance} XAF")
    print(f"   - Solde business location: {business_location_wallet.balance} XAF")
    
    # 8. Vérifier les transactions
    print("\n8. Transactions récentes:")
    
    # Récupérer les transactions liées au wallet utilisateur (GenericForeignKey)
    user_wallet_ct = ContentType.objects.get_for_model(user_wallet)
    user_transactions = UserTransaction.objects.filter(wallet_content_type=user_wallet_ct, wallet_object_id=user_wallet.id).order_by('-created_at')[:3]
    print(f"   - Transactions utilisateur ({user_transactions.count()}):")
    for t in user_transactions:
        print(f"     * {t.created_at.strftime('%H:%M')} - {t.get_transaction_type_display()} - {t.amount} XAF - {t.description}")
    
    # Récupérer les transactions liées au wallet business location (GenericForeignKey)
    bl_wallet_ct = ContentType.objects.get_for_model(business_location_wallet)
    business_transactions = UserTransaction.objects.filter(wallet_content_type=bl_wallet_ct, wallet_object_id=business_location_wallet.id).order_by('-created_at')[:3]
    print(f"   - Transactions business location ({business_transactions.count()}):")
    for t in business_transactions:
        print(f"     * {t.created_at.strftime('%H:%M')} - {t.get_transaction_type_display()} - {t.amount} XAF - {t.description}")
    
    print("\n=== TEST TERMINÉ ===")

if __name__ == '__main__':
    test_wallet_system() 