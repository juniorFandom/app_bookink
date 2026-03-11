#!/usr/bin/env python
"""
Script pour ajouter des images de test aux sites touristiques
"""
import os
import sys
import django
import requests
from io import BytesIO
from django.core.files import File

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tourist_sites.models import TouristSite, TouristSiteImage

def download_image(url, filename):
    """Télécharge une image depuis une URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content), filename
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
        return None, None

def create_test_images():
    print("Ajout d'images de test aux sites touristiques...")
    
    # Images de test pour chaque site (URLs d'images libres de droits)
    site_images = {
        'Parc National de Waza': [
            'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800&h=600&fit=crop',
        ],
        'Mont Cameroun': [
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1464822759844-d150baec0134?w=800&h=600&fit=crop',
        ],
        'Plage de Kribi': [
            'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop',
        ],
        'Foumban': [
            'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
        ],
        'Parc National de Korup': [
            'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800&h=600&fit=crop',
        ]
    }
    
    sites = TouristSite.objects.all()
    
    for site in sites:
        print(f"\nTraitement du site: {site.name}")
        
        # Vérifier si le site a déjà des images
        if site.images.exists():
            print(f"  ⚠ Le site {site.name} a déjà {site.images.count()} image(s)")
            continue
        
        # Récupérer les URLs d'images pour ce site
        image_urls = site_images.get(site.name, [])
        
        if not image_urls:
            print(f"  ⚠ Aucune image de test définie pour {site.name}")
            continue
        
        # Ajouter les images
        for i, image_url in enumerate(image_urls):
            print(f"  📥 Téléchargement de l'image {i+1}/{len(image_urls)}...")
            
            image_data, filename = download_image(image_url, f"{site.name.lower().replace(' ', '_')}_{i+1}.jpg")
            
            if image_data:
                try:
                    # Créer l'objet TouristSiteImage
                    site_image = TouristSiteImage(
                        site=site,
                        caption=f"Image {i+1} de {site.name}",
                        is_primary=(i == 0)  # La première image est primaire
                    )
                    
                    # Sauvegarder l'image
                    site_image.image.save(filename, File(image_data), save=True)
                    print(f"  ✅ Image {i+1} ajoutée avec succès")
                    
                except Exception as e:
                    print(f"  ❌ Erreur lors de la sauvegarde de l'image {i+1}: {e}")
            else:
                print(f"  ❌ Impossible de télécharger l'image {i+1}")
    
    print("\n✅ Script terminé!")
    print(f"📊 Statistiques des images:")
    
    for site in sites:
        image_count = site.images.count()
        print(f"   - {site.name}: {image_count} image(s)")

if __name__ == '__main__':
    create_test_images() 