# Business Administration System

Ce module fournit un système d'administration complet pour gérer les entreprises, leurs emplacements et les avis clients.

## Fonctionnalités

### 🔐 Sécurité
- **Authentification requise** : Toutes les vues nécessitent une connexion
- **Permissions staff** : Seuls les utilisateurs avec `is_staff=True` peuvent accéder
- **Protection CSRF** : Toutes les actions POST sont protégées

### 📊 Tableau de bord
- **Statistiques en temps réel** : Nombre total d'entreprises, actives, vérifiées
- **Activité récente** : Dernières entreprises créées
- **Actions rapides** : Liens directs vers les fonctionnalités principales

### 🏢 Gestion des entreprises
- **Liste avec filtres** : Recherche, statut, vérification
- **Création/Édition** : Formulaires complets avec validation
- **Détails complets** : Informations, emplacements, statistiques
- **Actions rapides** : Activer/désactiver, vérifier/dévérifier
- **Suppression sécurisée** : Vérification des dépendances

### 📍 Gestion des emplacements
- **Tableau de bord dédié** : Statistiques par type d'entreprise
- **Liste filtrée** : Par type, statut, vérification, mise en avant
- **Gestion des images** : Upload, suppression, image principale
- **Actions de statut** : Actif/inactif, vérifié/non vérifié, mis en avant

### ⭐ Modération des avis
- **Tableau de bord des avis** : Statistiques et tendances
- **Liste avec filtres** : Par note, emplacement, type de visite
- **Modération** : Approuver/rejeter les avis
- **Analytics** : Distribution des notes, tendances mensuelles

## Structure des URLs

```
/admin/business/
├── dashboard/                    # Tableau de bord principal
├── business/                     # Gestion des entreprises
│   ├── /                        # Liste des entreprises
│   ├── create/                  # Créer une entreprise
│   ├── <pk>/                    # Détails d'une entreprise
│   ├── <pk>/edit/               # Éditer une entreprise
│   ├── <pk>/delete/             # Supprimer une entreprise
│   ├── <pk>/toggle-status/      # Activer/désactiver
│   └── <pk>/toggle-verification/ # Vérifier/dévérifier
├── location/                    # Gestion des emplacements
│   ├── dashboard/               # Tableau de bord des emplacements
│   ├── /                        # Liste des emplacements
│   ├── create/                  # Créer un emplacement
│   ├── <pk>/                    # Détails d'un emplacement
│   ├── <pk>/edit/               # Éditer un emplacement
│   ├── <pk>/delete/             # Supprimer un emplacement
│   ├── <pk>/toggle-status/      # Activer/désactiver
│   ├── <pk>/toggle-verification/ # Vérifier/dévérifier
│   ├── <pk>/toggle-featured/    # Mettre en avant
│   ├── <pk>/image/<id>/delete/  # Supprimer une image
│   └── <pk>/image/<id>/primary/ # Définir comme image principale
└── review/                      # Gestion des avis
    ├── dashboard/               # Tableau de bord des avis
    ├── /                        # Liste des avis
    ├── <pk>/                    # Détails d'un avis
    ├── <pk>/edit/               # Éditer un avis
    ├── <pk>/delete/             # Supprimer un avis
    ├── <pk>/approve/            # Approuver un avis
    ├── <pk>/reject/             # Rejeter un avis
    └── analytics/               # Analytics des avis
```

## Templates

### Structure des templates
```
templates/business/admin/
├── base.html                    # Template de base avec sidebar
├── dashboard.html               # Tableau de bord principal
├── business/
│   ├── business_list.html       # Liste des entreprises
│   ├── business_form.html       # Formulaire création/édition
│   └── business_detail.html     # Détails d'une entreprise
├── location/
│   ├── location_dashboard.html  # Tableau de bord des emplacements
│   ├── location_list.html       # Liste des emplacements
│   ├── location_form.html       # Formulaire création/édition
│   └── location_detail.html     # Détails d'un emplacement
└── review/
    ├── review_dashboard.html    # Tableau de bord des avis
    ├── review_list.html         # Liste des avis
    ├── review_form.html         # Formulaire édition
    ├── review_detail.html       # Détails d'un avis
    └── review_analytics.html    # Analytics des avis
```

### Design
- **Interface moderne** : Bootstrap 5 avec design responsive
- **Sidebar navigation** : Navigation claire et intuitive
- **Cartes interactives** : Statistiques avec animations
- **Tableaux filtrés** : Recherche et tri avancés
- **Actions rapides** : Boutons pour les opérations courantes

## Utilisation

### Accès
1. Connectez-vous avec un compte staff
2. Naviguez vers `/business/admin/dashboard/`
3. Utilisez la sidebar pour naviguer entre les sections

### Permissions requises
```python
# L'utilisateur doit avoir is_staff=True
def is_staff_user(user):
    return user.is_authenticated and user.is_staff
```

### Exemple d'utilisation
```python
# Dans une vue Django
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.business.views.admin.business import is_staff_user

@login_required
@user_passes_test(is_staff_user)
def my_admin_view(request):
    # Votre logique d'administration
    pass
```

## Fonctionnalités avancées

### AJAX
- **Toggle de statut** : Changement en temps réel sans rechargement
- **Upload d'images** : Interface drag & drop pour les images
- **Notifications** : Messages de succès/erreur dynamiques

### Sécurité
- **Validation côté serveur** : Toutes les données sont validées
- **Protection CSRF** : Tokens CSRF sur toutes les actions POST
- **Permissions granulaires** : Vérification des permissions par action

### Performance
- **Pagination** : Chargement optimisé des listes
- **Requêtes optimisées** : `select_related` et `prefetch_related`
- **Cache** : Mise en cache des statistiques fréquemment utilisées

## Maintenance

### Logs
Toutes les actions d'administration sont loggées pour audit :
- Création/modification/suppression d'entreprises
- Changements de statut
- Actions de modération

### Sauvegarde
Il est recommandé de :
- Sauvegarder régulièrement la base de données
- Surveiller les logs d'administration
- Tester les fonctionnalités après les mises à jour

## Support

Pour toute question ou problème :
1. Vérifiez les logs Django
2. Consultez la documentation Django
3. Contactez l'équipe de développement 