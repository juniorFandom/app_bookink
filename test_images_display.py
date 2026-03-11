#!/usr/bin/env python
"""
Script de test pour vérifier l'affichage des images des sites touristiques
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tourist_sites.models import TouristSite, TouristSiteImage

def test_images_display():
    print("🔍 Test d'affichage des images des sites touristiques...")
    print("=" * 60)
    
    sites = TouristSite.objects.prefetch_related('images').all()
    
    if not sites.exists():
        print("❌ Aucun site touristique trouvé dans la base de données")
        return
    
    print(f"📊 Nombre total de sites: {sites.count()}")
    print()
    
    for site in sites:
        print(f"🏛️  Site: {site.name}")
        print(f"   📍 Coordonnées: {site.latitude}, {site.longitude}")
        print(f"   🏷️  Catégorie: {site.category.name if site.category else 'Aucune'}")
        
        images = site.images.all()
        print(f"   🖼️  Nombre d'images: {images.count()}")
        
        if images.exists():
            for i, image in enumerate(images, 1):
                print(f"      Image {i}:")
                print(f"         📁 Chemin: {image.image.name}")
                print(f"         🌐 URL: {image.image.url}")
                print(f"         📝 Légende: {image.caption}")
                print(f"         ⭐ Primaire: {'Oui' if image.is_primary else 'Non'}")
                
                # Vérifier si le fichier existe physiquement
                if os.path.exists(image.image.path):
                    print(f"         ✅ Fichier existe: Oui")
                    file_size = os.path.getsize(image.image.path)
                    print(f"         📏 Taille: {file_size} bytes")
                else:
                    print(f"         ❌ Fichier existe: Non")
                print()
        else:
            print("      ❌ Aucune image associée")
            print()
    
    print("=" * 60)
    print("✅ Test terminé!")
    
    # Statistiques globales
    total_images = TouristSiteImage.objects.count()
    sites_with_images = sites.filter(images__isnull=False).distinct().count()
    
    print(f"\n📈 Statistiques globales:")
    print(f"   - Total d'images: {total_images}")
    print(f"   - Sites avec images: {sites_with_images}/{sites.count()}")
    print(f"   - Sites sans images: {sites.count() - sites_with_images}")

if __name__ == '__main__':
    test_images_display() 