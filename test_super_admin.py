#!/usr/bin/env python
"""
Script de test pour le dashboard super administrateur
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.business.models import Business, BusinessLocation
from apps.wallets.models import UserTransaction, BusinessLocationWallet
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def create_super_user():
    """Créer un super utilisateur pour tester le dashboard"""
    username = 'superadmin'
    email = 'superadmin@example.com'
    password = 'superadmin123'
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        print(f"L'utilisateur {username} existe déjà")
        return User.objects.get(username=username)
    
    # Créer le super utilisateur
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print(f"Super utilisateur créé avec succès:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"URL du dashboard: http://127.0.0.1:8000/business/super-admin/dashboard/")
    
    return user

def create_test_data():
    """Créer des données de test pour le dashboard"""
    print("Création des données de test...")
    
    # Créer un business de test
    business, created = Business.objects.get_or_create(
        name="Business Test",
        defaults={
            'email': 'test@business.com',
            'phone': '+237123456789',
            'description': 'Business de test pour le dashboard'
        }
    )
    
    # Créer des business locations non vérifiées
    for i in range(3):
        location, created = BusinessLocation.objects.get_or_create(
            name=f"Location Test {i+1}",
            business=business,
            defaults={
                'phone': f'+23712345678{i}',
                'email': f'test{i}@location.com',
                'registration_number': f'REG{i:03d}',
                'description': f'Description de la location test {i+1}',
                'business_location_type': 'hotel' if i == 0 else 'restaurant' if i == 1 else 'tour_operator',
                'is_verified': False,
                'is_active': True
            }
        )
        
        if created:
            print(f"Business location créée: {location.name}")
    
    # Créer des transactions de test
    wallet, created = BusinessLocationWallet.objects.get_or_create(
        business_location=business.locations.first()
    )
    
    # Créer quelques transactions
    for i in range(5):
        transaction = UserTransaction.objects.create(
            wallet=wallet,
            amount=10000 + (i * 5000),  # 10k à 30k XAF
            transaction_type='PAYMENT',
            status='COMPLETED',
            description=f'Transaction de test {i+1}',
            reference=f'REF{i:03d}'
        )
        print(f"Transaction créée: {transaction.reference} - {transaction.amount} XAF")
    
    print("Données de test créées avec succès!")

def main():
    """Fonction principale"""
    print("=== Test Dashboard Super Administrateur ===")
    
    # Créer le super utilisateur
    super_user = create_super_user()
    
    # Créer des données de test
    create_test_data()
    
    print("\n=== Instructions ===")
    print("1. Démarrez le serveur Django: python manage.py runserver")
    print("2. Connectez-vous avec:")
    print(f"   Username: {super_user.username}")
    print(f"   Password: superadmin123")
    print("3. Accédez au dashboard: http://127.0.0.1:8000/business/super-admin/dashboard/")
    print("4. Ou utilisez le lien dans le menu utilisateur (couronne)")

if __name__ == '__main__':
    main() 