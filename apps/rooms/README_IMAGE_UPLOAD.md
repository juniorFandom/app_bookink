# Système d'Upload d'Images pour les Chambres

## Vue d'ensemble

Le système d'upload d'images pour les chambres utilise une approche hybride :
- **Images temporaires** pour les nouvelles chambres (stockage en session)
- **Images directes** pour les chambres existantes (association immédiate)

## Architecture

### 1. Images Temporaires (Nouvelles Chambres)

**Workflow :**
1. L'utilisateur upload des images → stockées avec `room=None`
2. Les IDs sont sauvegardés en session (`room_temp_images`)
3. Lors de la création de la chambre → association des images temporaires
4. Nettoyage de la session

**Endpoints :**
- `POST /rooms/upload-image-temp/` - Upload temporaire
- `POST /rooms/delete-image-temp/<id>/` - Suppression temporaire
- `GET /rooms/list-image-temp/` - Liste des images temporaires

### 2. Images Directes (Chambres Existantes)

**Workflow :**
1. L'utilisateur upload des images → association immédiate à la chambre
2. Gestion de l'ordre et des légendes en temps réel

**Endpoints :**
- `POST /rooms/<room_id>/upload-image/` - Upload direct
- `POST /rooms/<room_id>/delete-image/<id>/` - Suppression directe
- `POST /rooms/<room_id>/reorder-images/` - Réordonnancement

## Fonctionnalités

### Validation
- **Types supportés** : JPEG, PNG, GIF, WebP
- **Taille maximale** : 5MB par image
- **Limite** : 10 images par chambre
- **Permissions** : Vérification du propriétaire de l'établissement

### Interface Utilisateur
- **Drag & Drop** avec feedback visuel
- **Prévisualisation** en temps réel
- **Réordonnancement** avec boutons haut/bas
- **Légendes** éditables
- **Barre de progression** pendant l'upload
- **Messages d'erreur/succès**

### Sécurité
- **CSRF protection** sur tous les endpoints
- **Validation côté serveur** et client
- **Permissions utilisateur** vérifiées
- **Nettoyage automatique** des images orphelines

## Nettoyage Automatique

### Commande de Management
```bash
# Nettoyer les images temporaires de plus de 1 jour
python manage.py cleanup_temp_images

# Nettoyer les images de plus de 7 jours
python manage.py cleanup_temp_images --days 7

# Voir ce qui serait supprimé sans le faire
python manage.py cleanup_temp_images --dry-run
```

### Nettoyage en Session
- Suppression automatique lors de la création de chambre
- Nettoyage des images orphelines lors de la navigation

## Utilisation

### JavaScript
```javascript
// Upload d'image
const formData = new FormData();
formData.append('image', file);
formData.append('csrfmiddlewaretoken', token);

fetch('/rooms/upload-image-temp/', {
    method: 'POST',
    body: formData
});

// Suppression d'image
fetch(`/rooms/delete-image-temp/${imageId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': token }
});
```

### Python
```python
# Création d'image temporaire
temp_img = RoomImage.objects.create(
    room=None,
    image=image_file,
    caption='',
    order=0
)

# Association à une chambre
temp_img.room = room
temp_img.save()
```

## Migration depuis l'Ancien Système

Le système est conçu pour être **rétrocompatible** :
- Les chambres existantes continuent d'utiliser l'upload direct
- Les nouvelles chambres utilisent le système temporaire
- Aucune migration de données nécessaire

## Maintenance

### Surveillance
- Surveiller l'espace disque utilisé par les images temporaires
- Exécuter régulièrement la commande de nettoyage
- Vérifier les logs d'erreur d'upload

### Optimisation
- Les images sont compressées automatiquement par Django
- Utilisation de `save=False` pour éviter les sauvegardes inutiles
- Gestion efficace de la session pour éviter les fuites mémoire 