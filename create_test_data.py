#!/usr/bin/env python
"""
Script pour créer des données de test pour les sites touristiques
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tourist_sites.models import TouristSiteCategory, TouristSite

def create_test_data():
    print("Création des données de test pour les sites touristiques...")
    
    # Créer des catégories
    categories_data = [
        {
            'name': 'Parcs Nationaux',
            'description': 'Parcs nationaux et réserves naturelles du Cameroun'
        },
        {
            'name': 'Plages',
            'description': 'Plages et côtes du Cameroun'
        },
        {
            'name': 'Montagnes',
            'description': 'Montagnes et volcans du Cameroun'
        },
        {
            'name': 'Villes Historiques',
            'description': 'Villes avec un patrimoine historique important'
        },
        {
            'name': 'Sites Culturels',
            'description': 'Sites culturels et traditionnels'
        }
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = TouristSiteCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"✓ Catégorie créée: {category.name}")
        else:
            print(f"⚠ Catégorie existante: {category.name}")
        categories.append(category)
    
    # Créer des sites touristiques
    sites_data = [
        {
            'name': 'Parc National de Waza',
            'description': 'Le plus grand parc national du Cameroun, connu pour sa faune sauvage abondante.',
            'category': 'Parcs Nationaux',
            'latitude': 11.3333,
            'longitude': 14.6333
        },
        {
            'name': 'Mont Cameroun',
            'description': 'Le plus haut sommet d\'Afrique de l\'Ouest, volcan actif avec une vue imprenable.',
            'category': 'Montagnes',
            'latitude': 4.2167,
            'longitude': 9.1667
        },
        {
            'name': 'Plage de Kribi',
            'description': 'Magnifique plage de sable blanc avec des chutes d\'eau qui se jettent dans l\'océan.',
            'category': 'Plages',
            'latitude': 2.9333,
            'longitude': 9.9167
        },
        {
            'name': 'Foumban',
            'description': 'Capitale du royaume Bamoun, riche en histoire et culture traditionnelle.',
            'category': 'Villes Historiques',
            'latitude': 5.7167,
            'longitude': 10.9167
        },
        {
            'name': 'Parc National de Korup',
            'description': 'Une des plus anciennes forêts tropicales du monde, avec une biodiversité exceptionnelle.',
            'category': 'Parcs Nationaux',
            'latitude': 5.0833,
            'longitude': 8.8333
        }
    ]
    
    for site_data in sites_data:
        category = next((cat for cat in categories if cat.name == site_data['category']), None)
        
        site, created = TouristSite.objects.get_or_create(
            name=site_data['name'],
            defaults={
                'description': site_data['description'],
                'category': category,
                'latitude': site_data['latitude'],
                'longitude': site_data['longitude'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✓ Site créé: {site.name}")
        else:
            print(f"⚠ Site existant: {site.name}")
    
    print("\n✅ Données de test créées avec succès!")
    print(f"📊 Statistiques:")
    print(f"   - Catégories: {TouristSiteCategory.objects.count()}")
    print(f"   - Sites: {TouristSite.objects.count()}")

if __name__ == '__main__':
    create_test_data() 