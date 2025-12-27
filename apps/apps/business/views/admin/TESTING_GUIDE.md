# Guide de Test - Système d'Administration Business

## Prérequis

### 1. Installation des dépendances
```bash
# Installer les dépendances Django
pip install -r requirements.txt

# Ou installer Django directement
pip install Django==5.2.2
```

### 2. Configuration de la base de données
```bash
# Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

## Test du système

### 1. Démarrer le serveur
```bash
python manage.py runserver
```

### 2. Accéder au système d'administration
- URL : `http://localhost:8000/business/admin/dashboard/`
- Connectez-vous avec votre compte superutilisateur

### 3. Points de test

#### ✅ Tableau de bord principal
- [ ] Statistiques s'affichent correctement
- [ ] Cartes interactives fonctionnent
- [ ] Navigation sidebar fonctionne
- [ ] Actions rapides redirigent correctement

#### ✅ Gestion des entreprises
- [ ] Liste des entreprises avec filtres
- [ ] Création d'une nouvelle entreprise
- [ ] Édition d'une entreprise existante
- [ ] Détails d'une entreprise
- [ ] Toggle status (actif/inactif)
- [ ] Toggle vérification
- [ ] Suppression d'entreprise

#### ✅ Gestion des emplacements
- [ ] Tableau de bord des emplacements
- [ ] Liste avec filtres avancés
- [ ] Création d'emplacement
- [ ] Gestion des images
- [ ] Toggle status, vérification, featured
- [ ] Détails d'emplacement

#### ✅ Gestion des avis
- [ ] Tableau de bord des avis
- [ ] Liste avec filtres
- [ ] Modération (approuver/rejeter)
- [ ] Analytics des avis
- [ ] Détails d'avis

## Fonctionnalités à tester

### 🔐 Sécurité
- [ ] Seuls les utilisateurs staff peuvent accéder
- [ ] Protection CSRF sur toutes les actions POST
- [ ] Validation des permissions

### 📱 Interface utilisateur
- [ ] Design responsive (mobile, tablet, desktop)
- [ ] Navigation intuitive
- [ ] Messages d'erreur et de succès
- [ ] Pagination fonctionnelle

### ⚡ Performance
- [ ] Chargement rapide des pages
- [ ] Requêtes optimisées
- [ ] Pagination efficace

### 🔄 Actions AJAX
- [ ] Toggle de statut sans rechargement
- [ ] Messages de confirmation
- [ ] Gestion des erreurs

## Cas d'usage de test

### 1. Création complète d'une entreprise
```bash
# 1. Aller sur /business/admin/business/create/
# 2. Remplir le formulaire
# 3. Vérifier la création
# 4. Ajouter des emplacements
# 5. Tester les actions de statut
```

### 2. Modération d'avis
```bash
# 1. Aller sur /business/admin/review/
# 2. Filtrer par statut
# 3. Approuver/rejeter des avis
# 4. Vérifier les changements
```

### 3. Gestion des images
```bash
# 1. Aller sur un emplacement
# 2. Uploader des images
# 3. Définir une image principale
# 4. Supprimer des images
```

## Dépannage

### Erreurs courantes

#### 1. ModuleNotFoundError: No module named 'django'
```bash
# Solution : Installer Django
pip install Django==5.2.2
```

#### 2. TemplateDoesNotExist
```bash
# Vérifier que les templates sont dans le bon dossier
# apps/business/templates/business/admin/
```

#### 3. URL not found
```bash
# Vérifier la configuration des URLs
# apps/business/urls.py et apps/business/views/admin/urls.py
```

#### 4. Permission denied
```bash
# Vérifier que l'utilisateur a is_staff=True
# Dans l'admin Django : /admin/auth/user/
```

### Logs de débogage
```python
# Dans settings.py, activer le debug
DEBUG = True

# Vérifier les logs Django
python manage.py runserver --verbosity=2
```

## Améliorations futures

### Fonctionnalités à ajouter
- [ ] Export de données (CSV, Excel)
- [ ] Notifications par email
- [ ] Logs d'audit détaillés
- [ ] API REST pour l'administration
- [ ] Tableau de bord avec graphiques
- [ ] Système de rôles et permissions

### Optimisations
- [ ] Cache des statistiques
- [ ] Pagination infinie
- [ ] Recherche en temps réel
- [ ] Filtres avancés

## Support

En cas de problème :
1. Vérifier les logs Django
2. Consulter la documentation Django
3. Tester avec un environnement propre
4. Vérifier les permissions utilisateur

## Commandes utiles

```bash
# Vérifier l'état des migrations
python manage.py showmigrations

# Créer des données de test
python manage.py shell
>>> from apps.business.models import Business
>>> Business.objects.create(name="Test Business", email="test@example.com", phone="1234567890")

# Vérifier les URLs
python manage.py show_urls | grep admin

# Tester les vues
python manage.py test apps.business.tests
``` 